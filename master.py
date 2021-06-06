from instructions import Layer, send, Instruction, create, connect, disconnect, mac, send_frame, ip, send_packet
from switch import Host, Data, Switch
from hub import Hub


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
    write(layer.devices)
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


def write(devices: list):
    devices.sort()
    file = open("output/devices.bin", 'a')
    for device in devices:
        file.write("device={}, name={}".format(str(type(device)).split('\'')[1].split('.')[0], device.name))
        if type(device) != Host:
            file.write(", ports_number={}".format(device.ports_number))
        if type(device) != Hub:
            device_mac = device.mac
            mac_address = device_mac
            if type(device) != Host:
                mac_address = "["
                for i in range(len(device_mac)):
                    mac_address += device_mac[i]
                    if i < len(device_mac) - 1:
                        mac_address += ", "
                mac_address += "]"
            file.write(", mac={}".format(mac_address))
            if type(device) != Switch:
                ip_address = device.ip
                ip_address = "{}.{}.{}.{}".format(ip_address[0], ip_address[1], ip_address[2], ip_address[3])
                file.write(", ip={}".format(ip_address))
        file.write("\n")
    file.close()
