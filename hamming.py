
def encode(data: list):
    if len(data) < 1:
        return []
    return parity_bits(data)


def decode(data: list, code: list):
    if len(code) < 1:
        return len(data) < 1
    return parity_bits(data) == code


def parity_bits(data: list):
    code, c = redundant_bits(data)
    n = len(code)
    p = 1
    bits = []
    for i in range(c):
        value = 0
        for j in range(1, n + 1):
            if j & p == p:
                value = value ^ code[-j]
        bits.append(value)
        p *= 2
    return bits


def redundant_bits(data: list):
    c = count(len(data))
    p = 1
    k = 1
    code = []
    for i in range(1, len(data) + c + 1):
        if i == p:
            code.append(0)
            p *= 2
        else:
            code.append(data[-k])
            k += 1
    return code[::-1], c


def count(m: int):
    p = 1
    n = m + 1
    for i in range(m):
        if p >= n:
            return i
        p *= 2
        n += 1
    return 0
