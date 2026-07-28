SUPPORTED_TYPES = {
    "boolean",
    "float",
    "double",
    "int8",
    "int16",
    "int32",
    "uint8",
    "uint16",
    "uint32",
    "string",
}


def validate(collection):

    paths = set()

    for s in collection.signals:

        if s.datatype not in SUPPORTED_TYPES:
            raise ValueError(
                f"{s.path}: invalid datatype"
            )

        if s.path in paths:
            raise ValueError(
                f"{s.path}: duplicate"
            )

        paths.add(s.path)