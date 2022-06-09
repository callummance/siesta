
from abc import abstractmethod
from io import BufferedReader
import os
import sys
from typing import Callable, Literal

STR_BUF_LEN: int = 1024


class Binary:
    """Binary represents a chunk of binary data, whether that comes from a file or other source"""
    endianness: Literal["little", "big"]

    @abstractmethod
    def get_bytes(self, start: int, length: int, func: Callable[[bytes], bytes] | None) -> bytes:
        """get_bytes retrieves `length` bytes starting at byte `start`

        Optionally a function `f` may be provided, which will be applied to the entire buffer. If the
        chosen range goes beyond the end of the file, fewer bytes will be returned.
        """

        pass

    @abstractmethod
    def get_size(self) -> int:
        """get_size retrieves the size of the binary in bytes.
        """

        pass

    def get_i64(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_i64 returns the 8 bytes starting at loc interpreted as a signed 64-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 8, func), self.endianness, signed=True)

    def get_u64(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_u64 returns the 8 bytes starting at loc interpreted as a signed 64-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 8, func), self.endianness, signed=False)

    def get_i32(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_i32 returns the 8 bytes starting at loc interpreted as a signed 32-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 4, func), self.endianness, signed=True)

    def get_u32(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_u32 returns the 8 bytes starting at loc interpreted as a signed 32-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 4, func), self.endianness, signed=False)

    def get_i16(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_i16 returns the 8 bytes starting at loc interpreted as a signed 16-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 2, func), self.endianness, signed=True)

    def get_u16(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_i16 returns the 8 bytes starting at loc interpreted as a signed 16-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 2, func), self.endianness, signed=False)

    def get_i8(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_i8 returns the 8 bytes starting at loc interpreted as a signed 8-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 1, func), self.endianness, signed=True)

    def get_u8(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> int:
        """get_u8 returns the 8 bytes starting at loc interpreted as a signed 8-bit integer"""
        return int.from_bytes(self.get_bytes(loc, 1, func), self.endianness, signed=False)

    def get_cstring(self, loc: int, func: Callable[[bytes], bytes] | None = None) -> bytes:
        """get_cstring returns a bytes object containing a c-style (null-terminated) string starting at location `loc`.

        Optionally a function `f` may be provided, which will be applied to each block of data as it
        is read. If no null byte is found before the end of the buffer, will instead just return all bytes
        from the staring location until the end of the buffer.
        """

        buf = bytearray()
        cur_loc = loc
        while True:
            chunk = self.get_bytes(cur_loc, STR_BUF_LEN, func=func)
            buf += chunk
            if b'\x00' in buf:
                end_idx = buf.find(b'\x00')
                del buf[end_idx:]
                break
            elif len(chunk) < STR_BUF_LEN:
                break
            else:
                cur_loc += len(chunk)

        return bytes(buf)


class BinaryFile(Binary):
    """BinaryFile represents binary data loaded from a file"""
    path: str
    comment: str
    endianness: Literal["little", "big"]

    def __init__(self, path: str, comment: str, endianness: Literal["little", "big"] = sys.byteorder):
        self.path = path
        self.comment = comment
        self.endianness = endianness

    def __get_file_handle(self) -> BufferedReader:
        return open(self.path, "rb")

    def get_bytes(self, start: int, length: int, func: Callable[[bytes], bytes] | None = None) -> bytes:
        """get_bytes retrieves `length` bytes starting at byte `start`

        Optionally a function `f` may be provided, which will be applied to the entire buffer. If the
        chosen range goes beyond the end of the file, fewer bytes will be returned.
        """

        with self.__get_file_handle() as file:
            file.seek(start)
            data: bytes = file.read(length)
            if func is not None:
                data = func(data)
            return bytes(data)

    def get_size(self) -> int:
        with self.__get_file_handle() as file:
            file.seek(0, os.SEEK_END)
            return file.tell()


class BinaryBlock(Binary):
    """BinaryBlock represents a block of binary data found at an offset within another Binary"""
    underlying_bin: Binary
    offset: int
    endianness: Literal["little", "big"]
    length: int

    def __init__(self, underlying: Binary, offset: int, length: int):
        self.underlying_bin = underlying
        self.offset = offset
        self.endianness = underlying.endianness
        self.length = length

    def get_bytes(self, start: int, length: int, func: Callable[[bytes], bytes] | None) -> bytes:
        """get_bytes retrieves `length` bytes starting at byte `start` from the start of this block

        Optionally a function `f` may be provided, which will be applied to the entire buffer. If the
        chosen range goes beyond the end of the file, fewer bytes will be returned.
        """

        return self.underlying_bin.get_bytes(start + self.offset, length, func)

    def get_size(self) -> int:
        return self.length
