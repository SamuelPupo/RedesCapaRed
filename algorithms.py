from objects import Detection
from crc import encode as encode_c, decode as decode_c
from hamming import encode as encode_h, decode as decode_h


def define(error_detection: str):
    if error_detection == "HAMMING":
        return Detection.HAMMING
    if error_detection == "CRC":
        return Detection.CRC
    print("\nUNRECOGNIZED ALGORITHM.")
    raise Exception


def create(error_detection: Detection, data: list):
    if error_detection == Detection.HAMMING:
        return encode_h(data)
    elif error_detection == Detection.CRC:
        return encode_c(data)
    return []


def detect(error_detection: Detection, data: list, code: list):
    if len(data) < 1:
        return False
    if error_detection == Detection.HAMMING:
        return decode_h(data, code)
    elif error_detection == Detection.CRC:
        return not decode_c(code).__contains__(1)
    return []
