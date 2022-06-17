
from typing import Any, Callable, Optional, cast
import copy
from dataclasses import dataclass

from .field_data import FieldData
from .format import Field, NestedBlockField, StructField, UnknownField
from .binary import Binary, BinaryBlock


@dataclass
class ReaderOpts:
    """Options passed to a reader, controlling what data is read from the target binary"""
    include_gaps: bool = False


class Reader:
    """Class used to read an input binary and extract the provided fields from it"""
    fields: list[Field]
    opts: ReaderOpts
    vars: dict[str, Any]
    preprocess: Callable[[bytes], bytes] | None

    def __init__(self, fields: list[Field], options: ReaderOpts = ReaderOpts(), preprocess: Callable[[bytes], bytes] | None = None):
        self.fields = fields
        self.opts = options
        self.vars = {}
        self.preprocess = preprocess

    def __should_fill_blanks(self) -> bool:
        return self.opts.include_gaps

    def __get_next_field(self, queue: list[Field], loc: int, binary_size: Optional[int]) -> Field | None:
        # If we are already at the end of the binary, return none
        if binary_size is not None and loc >= binary_size:
            return None

        # If there are no more fields left in the queue, just return a single unknown field covering the
        # remainder of the binary, or None depending on options
        if len(queue) == 0:
            if binary_size is not None and self.__should_fill_blanks():
                return UnknownField(binary_size - loc, start=loc)
            else:
                return None

        # If we do still have remaining fields but the next one has not yet reached its starting point,
        # either skip forwards to the next field or return an Unknown Field until its start depending on
        # options
        next_starting_offset = queue[0].get_start()
        if next_starting_offset is not None and next_starting_offset > loc:
            if self.__should_fill_blanks():
                return UnknownField(next_starting_offset - loc, start=loc)
            else:
                return queue.pop(0)

        # If the next field has an unspecified starting point or starts at or before the current location
        # just return it
        if next_starting_offset is None or next_starting_offset <= loc:
            # TODO: Maybe log if next starting offset is less than loc as this is probably unintentional
            return queue.pop(0)

        # That should cover all cases
        assert False, "Unexpected case when choosing next field"

    def read_binary(self, binary: Binary) -> list[FieldData]:
        """read_binary applies the fields definition to the provided binary, returning a list of retrieved data"""

        cur_loc: int = 0
        fields: list[Field] = copy.deepcopy(self.fields)
        struct = StructField(0, binary.get_size(), None, fields)

        (_, res) = self.__consume_struct(struct, binary, cur_loc)

        return res.val

    def __consume_struct(self, fields: StructField, binary: Binary, loc: int) -> tuple[int, FieldData]:
        """__consume_struct reads struct-like data from the binary. A max length may optionally be specified"""

        cur_loc = loc
        queued_fields: list[Field] = copy.deepcopy(fields.fields)
        completed_fields: list[FieldData] = []

        while True:
            next_field: Field | None = self.__get_next_field(
                queued_fields, cur_loc, fields.length)
            if next_field is None:
                break

            cur_loc, data = self.__consume_field(next_field, binary, cur_loc)
            completed_fields.append(data)

        res = FieldData(fields.get_label(loc), "struct", loc, completed_fields)
        return (cur_loc, res)

    def __consume_field(self, field: Field, binary: Binary, cur_loc: int) -> tuple[int, FieldData]:
        start_override = field.get_start()
        start_byte: int = start_override if start_override is not None else cur_loc
        preprocessor = compose(self.preprocess, field.get_preprocessor())
        val: Optional[Any] = None
        new_loc = start_byte
        match field.get_type():
            case "unknown":
                val = binary.get_bytes(
                    start_byte, cast(UnknownField, field).length, func=preprocessor)
                new_loc = start_byte + len(val)
            case "u8":
                val = binary.get_u8(start_byte, func=preprocessor)
                new_loc = start_byte + 1
            case "i8":
                val = binary.get_i8(start_byte, func=preprocessor)
                new_loc = start_byte + 1
            case "u16":
                val = binary.get_u16(start_byte, func=preprocessor)
                new_loc = start_byte + 2
            case "i16":
                val = binary.get_i16(start_byte, func=preprocessor)
                new_loc = start_byte + 2
            case "u32":
                val = binary.get_u32(start_byte, func=preprocessor)
                new_loc = start_byte + 4
            case "i32":
                val = binary.get_i32(start_byte, func=preprocessor)
                new_loc = start_byte + 4
            case "u64":
                val = binary.get_u64(start_byte, func=preprocessor)
                new_loc = start_byte + 8
            case "i64":
                val = binary.get_i64(start_byte, func=preprocessor)
                new_loc = start_byte + 8
            case "nested":
                _field = cast(NestedBlockField, field)
                sub_reader: Reader = Reader(
                    _field.subfields, self.opts, preprocess=preprocessor)
                bin_block = BinaryBlock(
                    binary, start_byte, _field.get_length(self.vars))
                val = sub_reader.read_binary(bin_block)
            case _:
                pass

        name = field.get_name()
        if name is not None:
            self.vars[name] = val
        res = FieldData(field.get_label(start_byte),
                        field.get_type(), start_byte, val)
        return (new_loc, res)


def compose(block_preprocessor: Callable[[bytes], bytes] | None, field_preprocessor: Callable[[bytes], bytes] | None) -> Callable[[bytes], bytes] | None:
    """compose composes 2 optional functions, calling the block preprocessor first, then the field preprocessor on the result."""

    if block_preprocessor is None and field_preprocessor is None:
        return None
    elif block_preprocessor is None and field_preprocessor is not None:
        return field_preprocessor
    elif block_preprocessor is not None and field_preprocessor is None:
        return block_preprocessor
    elif callable(block_preprocessor) and callable(field_preprocessor) is not None:
        _field_preprocessor: Callable[[bytes], bytes] = cast(
            Callable[[bytes], bytes], field_preprocessor)
        _block_preprocessor: Callable[[bytes], bytes] = cast(
            Callable[[bytes], bytes], block_preprocessor)
        return lambda bs: _field_preprocessor(_block_preprocessor(bs))

    assert False
