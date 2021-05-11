from instructions import Layer, send, Instruction, create, connect, disconnect, mac, send_frame, ip, send_packet
from objects import Data
from switch import Host, Switch


def master(signal_time: int, error_detection: str, instructions: list):
    i = 0
    time = 0
    layer = Layer(signal_time, error_detection)
    sent = False
    while i < len(instructions) or sent:
        sent = False
        for device in layer.devices:
            if type(device) == Host and device.send(time) != Data.NULL or type(device) == Switch and device.send(time):
                sent = True
        if i < len(instructions):
            if time > instructions[i].time:
                print("\nWRONG INSTRUCTION TIME.")
                raise Exception
            if not sent and time < instructions[i].time:
                time = instructions[i].time
            j = i
            while j < len(instructions) and instructions[j].time == time:
                if controller(layer, instructions[j]):
                    sent = True
                j += 1
            i = j
        time += 1
    return time


def controller(layer: Layer, instruction: Instruction):
    if len(instruction.details) > 3:
        print("\nWRONG INSTRUCTION FORMAT.")
        raise Exception
    sent = False
    if instruction.command == "create":
        create(layer, instruction)
    elif instruction.command == "connect":
        connect(layer, instruction)
    elif instruction.command == "send":
        send(layer, instruction)
        sent = True
    elif instruction.command == "disconnect":
        disconnect(layer, instruction)
    elif instruction.command == "mac":
        mac(layer, instruction)
    elif instruction.command == "send_frame":
        send_frame(layer, instruction)
        sent = True
    elif instruction.command == "ip":
        ip(layer, instruction)
        sent = True
    elif instruction.command == "send_packet":
        send_packet(layer, instruction)
        sent = True
    else:
        print("\nUNRECOGNIZED INSTRUCTION.")
        raise Exception
    print("{} {}".format(instruction.time, instruction.command), end="")
    for i in range(len(instruction.details)):
        print(" {}".format(instruction.details[i]), end="")
    print()
    return sent
