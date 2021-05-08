
def string_to_hexadecimal(string: str):
    return int(string, 16) if len(string) > 0 else 0


def hexadecimal_to_binary(string: str):
    return [int(i) for i in bin(string_to_hexadecimal(string))[2:].zfill(len(string) * 4)] if len(string) > 0 else []


def decimal_to_binary(integer: int):
    return [int(i) for i in bin(integer)[2:].zfill(8)]


def binary_to_hexadecimal(binary: list):
    return str.upper(hex(binary_to_decimal(binary))[2:]) if len(binary) > 0 else ""


def binary_to_decimal(binary: list):
    return int("".join([str(b) for b in binary]), 2) if len(binary) > 0 else 0
