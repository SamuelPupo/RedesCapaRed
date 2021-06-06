from layer import Layer
from objects import Instruction


def create(layer: Layer, instruction: Instruction):
    details = instruction.details
    device = details[0]
    name = details[1]
    if device == "hub" or device == "switch":
        ports_number = int(details[2])
        if ports_number < 1:
            print("\nWRONG PORTS NUMBER.")
            raise Exception
    elif device == "host":
        if len(details) > 2:
            print("\nWRONG CREATE HOST INSTRUCTION FORMAT.")
            raise Exception
        ports_number = 1
    else:
        print("\nUNRECOGNIZED DEVICE TYPE.")
        raise Exception
    layer.create(device, name, ports_number)
    write(instruction.time, "create, device={}, name={}{}\n".format(device, name, ", ports_number={}".
                                                                    format(ports_number)
                                                                    if device == ("hub" or "switch") else ""))


def write(time: int, string: str):
    file = open("output/general.bin", 'a')
    file.write("time={}, instruction={}".format(time, string))
    file.close()


def connect(layer: Layer, instruction: Instruction):
    details = instruction.details
    if len(details) > 2:
        print("\nWRONG CONNECT INSTRUCTION FORMAT.")
        raise Exception
    port1 = reverse(details[0])
    port2 = reverse(details[1])
    layer.connect(instruction.time, port1[0], int(port1[1]) - 1, port2[0], int(port2[1]) - 1)
    write(instruction.time, "connect, device_x={}, port_x={}, device_y={}, port_y={}\n".format(port1[0], port1[1],
                                                                                               port2[0], port2[1]))


def reverse(port: str):
    # return port.split(':')
    port = port[::-1]
    port = port.split('_', 1)
    port = [x[::-1] for x in port]
    return port[::-1]


def send(layer: Layer, instruction: Instruction):
    details = instruction.details
    if len(details) > 2:
        print("\nWRONG SEND INSTRUCTION FORMAT.")
        raise Exception
    host = details[0]
    details = details[1]
    data = [int(details[i]) for i in range(len(details))]
    for i in range(len(data)):
        if data[i] != 0 and data[i] != 1:
            print("\nUNRECOGNIZED DATA TYPE.")
            raise Exception
    layer.send(instruction.time, host, data)
    write(instruction.time, "send, host={}, data={}\n".format(host, details))


def disconnect(layer: Layer, instruction: Instruction):
    details = instruction.details
    if len(details) > 1:
        print("\nWRONG DISCONNECT INSTRUCTION FORMAT.")
        raise Exception
    port = reverse(details[0])
    layer.disconnect(instruction.time, port[0], int(port[1]) - 1)
    write(instruction.time, "disconnect, device={}, port={}\n".format(port[0], port[1]))


def mac(layer: Layer, instruction: Instruction):
    details = instruction.details
    if len(details) > 2:
        print("\nWRONG MAC INSTRUCTION FORMAT.")
        raise Exception
    device = details[0].split(':')
    interface = int(device[1]) - 1 if len(device) > 1 else 0
    device = device[0]
    address = details[1]
    layer.mac(device, interface, address)
    write(instruction.time, "mac, device={}, address={}\n".format(details[0], address))


def send_frame(layer: Layer, instruction: Instruction):
    details = instruction.details
    host = details[0]
    destination_mac = details[1]
    data = details[2]
    layer.send_frame(instruction.time, host, destination_mac, data)
    write(instruction.time, "send_frame, host={}, destination_mac={}, data={}\n".format(host, destination_mac, data))


def ip(layer: Layer, instruction: Instruction):
    details = instruction.details
    host = details[0].split(':')
    interface = int(host[1]) - 1 if len(host) > 1 else 0
    host = host[0]
    address = details[1]
    mask = details[2]
    layer.ip(instruction.time, host, interface, address, mask)
    write(instruction.time, "ip, host={}, address={}, mask={}\n".format(details[0], address, mask))


def send_packet(layer: Layer, instruction: Instruction):
    details = instruction.details
    host = details[0]
    destination_ip = details[1]
    data = details[2]
    layer.send_packet(instruction.time, host, destination_ip, data)
    write(instruction.time, "send_packet, host={}, destination_ip={}, data={}\n".format(host, destination_ip, data))
