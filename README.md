# Siesta
A python framework for exploring and reverse engineering binary formats

## Simple example
```python
reader = Reader(fields=[
    IntField(32, False, name="f_size", start=0x04),
    IntField(32, False, name="book_size", start=0x08),
    NestedBlockField(0x11, "book_size", "body", [],
                     lambda bs: bytes(map(lambda b: b ^ 0x73, bs)))
], options=ReaderOpts(include_gaps=True))


bin = BinaryFile("/path/to/file.dat", "initial macros", endianness="little")

res = reader.read_binary(bin)
```

The above is the start of an attempt to read an FFXIV MACRO.dat file, extracting a field named "f_size" at address 0x04, another named "book_size" at 0x08, and a binary block at address 0x11 with length specified by the "book_size" variable. It is also XOR'd with 0x73.

## What works
- Struct-like lists of fields
- Integers
- Nested binary blocks
- Preprocessor functions

## To Do
- [ ] Arrays of fields
- [ ] Strings
- [ ] Literals
- [ ] File diffing
- [ ] File monitoring