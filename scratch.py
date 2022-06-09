from src import Reader, IntField, BinaryFile, NestedBlockField, ReaderOpts

reader = Reader(fields=[
    IntField(32, False, name="f_size", start=0x04),
    IntField(32, False, name="book_size", start=0x08),
    NestedBlockField(0x11, "book_size", "body", [],
                     lambda bs: bytes(map(lambda b: b ^ 0x73, bs)))
], options=ReaderOpts(include_gaps=True))


bin = BinaryFile("/mnt/Files/Projects/ff_datfiles/Global Macros/MACROSYS.dat",
                 "initial macros", endianness="little")

res = reader.read_binary(bin)


print(res[4])
