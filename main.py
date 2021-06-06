from os import mkdir, listdir, remove, path

from master import master, Instruction


def main():
    if not directory():
        return
    try:
        script = open("input/script.txt", 'r')
    except OSError:
        print("\nSCRIPT WAS NOT FOUND.\n")
        return
    signal_time = 10
    error_detection = "crc"
    try:
        config = open("input/config.txt", 'r')
    except OSError:
        print("\nCONFIG WAS NOT FOUND.\n")
    else:
        try:
            values = lines(config)
            for line in values:
                if len(line) < 1:
                    continue
                line = [x.strip() for x in line.split('=')]
                if line[0] == "signal_time":
                    signal_time = int(line[1])
                elif line[0] == "error_detection":
                    error_detection = line[1].lower()
                else:
                    print("\nWRONG CONFIG INSTRUCTION.")
                    raise Exception
        except Exception:
            print("\nCONFIG FORMAT ERROR.\n")
            signal_time = 10
            error_detection = "crc"
    try:  # Comment to debug
        print("\nCONNECTION STARTED.")
        print("(TIME = 0)\n")
        time = master(signal_time, error_detection, translator(script))
        script.close()
        print("\nCONNECTION ENDED.")
        print("(TIME = {})\n".format(time))
    except Exception:
        print("\nBAD FORMAT ERROR.\n")


def directory():
    try:
        mkdir("output")
    except OSError:
        try:
            for file in listdir("output"):
                remove(path.join("output", file))
        except OSError:
            print("\nOUTPUT DIRECTORY CLEANING FAILED.")
            return False
    return True


def lines(script):
    return [x.replace('\n', '').split('#')[0].strip() for x in script.readlines()]


def translator(script):
    values = lines(script)
    instructions = []
    for line in values:
        if len(line) > 0:
            line = line.split(' ')
            instructions.append(Instruction(int(line[0]), line[1], line[2:len(line)]))
    return instructions


if __name__ == '__main__':
    main()
