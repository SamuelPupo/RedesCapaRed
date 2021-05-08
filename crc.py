
key_ = [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def encode(data: list, key: list = None):
    if key is None:
        key = key_
    return data + mod2div(data + empty(len(key) - 1), key)


def decode(code: list, key: list = None):
    if key is None:
        key = key_
    return mod2div(code + empty(len(key) - 1), key)


def mod2div(dividend: list, divisor: list):
    pick = len(divisor)
    tmp = dividend[0: pick]
    while pick < len(dividend):
        tmp = xor(tmp, divisor if tmp[0] == 1 else empty(pick))
        tmp.append(dividend[pick])
        pick += 1
    return xor(tmp, divisor if tmp[0] == 1 else empty(pick))


def empty(length: int):
    return [0 for _ in range(length)]


def xor(a: list, b: list):
    n = min(len(a), len(b))
    return [(0 if a[i] == b[i] else 1) for i in range(1, n)]
