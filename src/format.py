

from abc import abstractmethod
from typing import Any, Callable, Optional

PreprocessorFunc = Optional[Callable[[bytes], bytes]]


class Field:
    """Field describes a single piece of data to be extracted from a binary"""
    @abstractmethod
    def get_type(self) -> str:
        """get_type returns a string describing the type of the field"""
        return "None"

    @abstractmethod
    def get_start(self) -> int | None:
        """get_start returns the starting offset of this field if specified or None if not"""

        pass

    @abstractmethod
    def get_preprocessor(self) -> PreprocessorFunc:
        """get_preprocessor returns the function that should be applied to the binary data before interpreting it"""

        pass

    @abstractmethod
    def get_name(self) -> str | None:
        """get_name returns this field's name"""

        pass

    def get_label(self, loc: int) -> str:
        """get_label returns this field's name if it has one, otherwise generates a sane default"""

        name = self.get_name()
        return name if name is not None else f"untitled_{self.get_type()}_field_{hex(loc)}"


class UnknownField(Field):
    """UnknownField will be automatically generated for unspecified regions in the binary
    if the option is selected"""
    start: int | None
    length: int

    def __init__(self, length: int, start: int | None = None):
        self.start = start
        self.length = length

    def get_type(self) -> str:
        return "unknown"

    def get_start(self) -> int | None:
        return self.start

    def get_preprocessor(self) -> PreprocessorFunc:
        return None

    def get_name(self) -> str | None:
        return None


class IntField(Field):
    """IntField represents a single integer value

    This may be 8, 16, 32 or 64 bits in size, and may be signed or unsigned."""
    start: int | None
    bits: int
    signed: bool
    preprocess: PreprocessorFunc
    name: str | None

    def __init__(self, bits: int, signed: bool, name: str | None = None, start: int | None = None, func: PreprocessorFunc = None):
        self.start = start
        if bits in [8, 16, 32, 64]:
            self.bits = bits
        else:
            print("Only 8-, 16-, 32- or 64-bit integers are supported. Defaulting to 32.")
            self.bits = 32
        self.signed = signed
        self.preprocess = func
        self.name = name

    def get_type(self) -> str:
        res = ""
        match self.signed:
            case True:
                res += "i"
            case False:
                res += "u"

        res += str(self.bits)
        return res

    def get_start(self) -> int | None:
        return self.start

    def get_preprocessor(self) -> PreprocessorFunc:
        return self.preprocess

    def get_name(self) -> str | None:
        return self.name


class NestedBlockField(Field):
    """"NestedField represents a block of memory which can contain other fields"""
    start: Optional[int]
    length: Optional[int | str]
    name: Optional[str]
    preprocessor: PreprocessorFunc
    subfields: list[Field]

    def __init__(self, start: Optional[int], length: Optional[int | str], name: Optional[str], subfields: list[Field], func: PreprocessorFunc = None):
        self.start = start
        self.length = length
        self.name = name
        self.preprocessor = func
        self.subfields = subfields

        if self.length is None:
            print(
                "NestedBlock Fields currently must have an explicit length provided upon creation")

    def get_type(self) -> str:
        return "nested"

    def get_start(self) -> int | None:
        return self.start

    def get_preprocessor(self) -> PreprocessorFunc:
        return self.preprocessor

    def get_name(self) -> str | None:
        return self.name

    def get_length(self, read_vars: dict[str, Any]) -> int:
        """get_length returns the length of this field in bytes"""

        if isinstance(self.length, str):
            # Look up variable
            res: Any = read_vars[self.length]
            if isinstance(res, int):
                return res
            else:
                raise ValueError(
                    f"The value of variable {self.length} was not an int or did not exist")
        elif isinstance(self.length, int):
            return self.length
        else:
            raise ValueError(
                "Size specification for a NestedBlockField must be an int or a string (name of variable)")


class StructField(Field):
    """StructField represents a struct-like block of data. It will contain a list of fields and may or may not have a set size."""

    start: Optional[int]
    length: Optional[int]
    fields: list[Field]
    preprocess: PreprocessorFunc
    name: Optional[str]

    def __init__(self, start: Optional[int], length: Optional[int], name: Optional[str], fields: list[Field], func: PreprocessorFunc = None):
        self.start = start
        self.length = length
        self.name = name
        self.preprocess = func
        self.fields = fields

    def get_name(self) -> str | None:
        return self.name

    def get_preprocessor(self) -> PreprocessorFunc:
        return self.preprocess

    def get_start(self) -> int | None:
        return self.start

    def get_type(self) -> str:
        return "struct"


class ArrayField(Field):
    pass
