from hub import Device, Data
from algorithms import define, detect, create
from converter import binary_to_hexadecimal, binary_to_decimal, hexadecimal_to_binary, decimal_to_binary


arpq_ = [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0]
arpr_ = [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1]


class Host(Device):
    def __init__(self, signal_time: int, error_detection: str, name: str, mac: str = "FFFF", ip: tuple = (0, 0, 0, 0),
                 mask: tuple = (0, 0, 0, 0)):
        super().__init__(name, 1)
        self.signal_time = signal_time
        self.error_detection = define(str.upper(error_detection))
        self.mac = mac
        self.ip = ip
        self.mask = mask
        self.subnet, self.broadcast = self.subnet_broadcast()
        self.table = dict()
        self.transmitting_started = -1
        self.data = []
        self.data_pointer = 0
        self.resend_attempts = 0
        self.waiting_packet = []
        self.receiving_data = [[] for _ in range(6)]
        self.receiving_data_pointer = [0, 0]
        self.start()

    def subnet_broadcast(self):
        ip = self.ip
        mask = self.mask
        subnet = [ip[i] & mask[i] for i in range(len(ip))]
        broadcast = subnet.copy()
        for i in range(len(subnet) - 1, -1, -1):
            if subnet[i] != 0:
                break
            broadcast[i] = 255
        return tuple(subnet), tuple(broadcast)

    def start(self):
        file = open("output/{}_data.txt".format(self.name), 'w')
        file.close()
        file = open("output/{}_payload.txt".format(self.name), 'w')
        file.close()

    def connect(self, time: int, port: int, other_device: Device, other_port: int):
        super().connect(time, port, other_device, other_port)
        if self.ports[0].data != Data.NULL:
            self.data_pointer += 1

    def disconnect(self, time: int, port: int):
        cable = self.ports[port]
        device = cable.device
        if device is None:
            return
        if len(self.data) > 0:
            device.receive_bit(time, cable.port, Data.NULL, True)
        if type(device) != Host and len(self.receiving_data[0]) > 0:
            self.receive_bit(time, cable.port, Data.NULL, True)
        super().disconnect(time, port)
        self.data_pointer = 0  # Comment if the the host must not restart sending data in case of disconnection

    def collision(self, string: str):
        super().collision(string)
        if self.data_pointer > 0:
            self.data_pointer -= 1  # Comment if the the host must not wait to resend data in case of collision
        self.resend_attempts += 1
        if self.resend_attempts == 50:
            self.reset()
        self.ports[0].data = Data.NULL

    def reset(self):
        self.data.pop(0)
        if len(self.data) < 1:
            self.transmitting_started = -1
        self.data_pointer = 0
        self.resend_attempts = 0
        self.ports[0].data = Data.NULL

    def receive_bit(self, time: int, port: int, data: Data, disconnected: bool = False):
        super().receive_bit(time, port, data, disconnected)
        self.write("\n")
        section = self.receiving_data_pointer[0]
        pointer = self.receiving_data_pointer[1]
        if data != Data.NULL:
            self.receiving_data[section].append(1 if data == Data.ONE else 0)
            self.receiving_data_pointer[1] += 1
            pointer += 1
            if ((section == 0 or section == 1) and pointer == 16) or \
                    (section == 4 and pointer == self.receiving_data[2]) or \
                    (section == 5 and pointer == self.receiving_data[3]):
                if section != 5:
                    if section != 4:
                        self.receiving_data[section] = binary_to_hexadecimal(self.receiving_data[section])
                    self.receiving_data_pointer[0] += 1
                    self.receiving_data_pointer[1] = 0
                else:
                    self.reset_receiving(time)
            elif (section == 2 or section == 3) and pointer == 8:
                self.receiving_data[section] = binary_to_decimal(self.receiving_data[section]) * 8
                self.receiving_data_pointer[0] += 1
                self.receiving_data_pointer[1] = 0
        else:
            if pointer > 0:
                if section == 0 or section == 1:
                    self.receiving_data[section] = binary_to_hexadecimal(self.receiving_data[section])
                elif section == 2 or section == 3:
                    self.receiving_data[section] = binary_to_decimal(self.receiving_data[section]) * 8
            self.reset_receiving(time)

    def reset_receiving(self, time: int):
        receiving_data = self.receiving_data
        destination = receiving_data[0]
        if destination == self.mac or destination == "FFFF":
            sender = receiving_data[1]
            data = receiving_data[4]
            state = "ERROR" if receiving_data[2] != len(receiving_data[4]) or \
                receiving_data[3] != len(receiving_data[5]) or \
                not detect(self.error_detection, receiving_data[4], receiving_data[5]) else "OK"
            if state != "ERROR":
                if len(data) == 64:
                    self.arp(time, data, str(sender))
                elif len(data) >= 88:
                    destination_ip = self.tuple_ip(data[:32])
                    if self.ip == destination_ip:
                        origen_ip = self.tuple_ip(data[32:64])
                        origen_ip = "{}.{}.{}.{}".format(origen_ip[0], origen_ip[1], origen_ip[2], origen_ip[3])
                        # ttl = data[64:72]
                        # protocol = data[72:80]
                        length = binary_to_decimal(data[80:88]) * 8
                        packet_data = binary_to_hexadecimal(data[88:])
                        self.write_payload(time, origen_ip,
                                           "data={}, state={}".format(packet_data if len(packet_data) > 0 else "NULL",
                                                                      "ERROR" if length / 4 != len(packet_data)
                                                                      else "OK"))
            self.write_data(time, str(sender), data, state)
        self.receiving_data = [[] for _ in range(6)]
        self.receiving_data_pointer = [0, 0]

    def arp(self, time: int, data: list, sender: str):
        arp = data[:32]
        destination_ip = self.tuple_ip(data[32:])
        origen_ip = "0.0.0.0"
        action = ""
        if arpq_ == arp:
            if self.ip == destination_ip:
                action = "ARPQ"
                self.arpr(time, hexadecimal_to_binary(sender))
        elif arpr_ == arp:
            self.table[tuple(destination_ip)] = sender
            origen_ip = "{}.{}.{}.{}".format(destination_ip[0], destination_ip[1], destination_ip[2], destination_ip[3])
            action = "ARPR"
            for p in self.waiting_packet:
                if p[0] == destination_ip:
                    self.send_packet(time, p[1], destination_ip)
                    break
        if len(action) > 0:
            self.write_payload(time, origen_ip, "action={}".format(action))

    @staticmethod
    def tuple_ip(destination_ip: list):
        return (binary_to_decimal(destination_ip[:8]), binary_to_decimal(destination_ip[8:16]),
                binary_to_decimal(destination_ip[16:24]), binary_to_decimal(destination_ip[24:]))

    def write_data(self, time: int, sender: str, data: list, state: str):
        file = open("output/{}_data.txt".format(self.name), 'a')
        data = binary_to_hexadecimal(data)
        file.write("time={}, host_mac={}, data={}, state={}\n\n".format(time, sender if len(sender) > 0 else "FFFF",
                                                                        data if len(data) > 0 else "NULL", state))
        file.close()

    def arpr(self, time: int, destination_mac: list = None):
        self.start_send(time, arpr_ + self.binary_ip(self.ip), destination_mac)

    def send_packet(self, time: int, data: list, destination_ip: tuple):
        binary_destination_ip = self.binary_ip(destination_ip)
        try:
            destination_mac = hexadecimal_to_binary(self.table[destination_ip])
        except Exception:
            self.waiting_packet.append((destination_ip, data))
            self.start_send(time, arpq_ + binary_destination_ip)
        else:
            origen_ip = self.binary_ip(self.ip)
            ttl = [0, 0, 0, 0, 0, 0, 0, 0]
            protocol = [0, 0, 0, 0, 0, 0, 0, 0]
            length = decimal_to_binary(int(len(data) / 8))
            self.start_send(time, binary_destination_ip + origen_ip + ttl + protocol + length + data, destination_mac)

    def write_payload(self, time: int, host_ip: str, string: str):
        file = open("output/{}_payload.txt".format(self.name), 'a')
        file.write("time={}, host_ip={}, {}\n\n".format(time, host_ip, string))
        file.close()

    @staticmethod
    def binary_ip(ip: tuple):
        return decimal_to_binary(ip[0]) + decimal_to_binary(ip[1]) + decimal_to_binary(ip[2]) + decimal_to_binary(ip[3])

    def start_send(self, time: int, data: list, destination_mac: list = None):
        if destination_mac is None:
            destination_mac = [1 for _ in range(16)]
        origen_mac = hexadecimal_to_binary(self.mac)
        data_length = decimal_to_binary(int(len(data) / 8))
        code = create(self.error_detection, data)
        code_length = decimal_to_binary(int(len(code) / 8))
        self.data.append(destination_mac + origen_mac + data_length + code_length + data + code)
        if len(self.data) == 1:
            self.transmitting_started = time
            self.send(time)

    def send(self, time: int, disconnected: bool = False):
        if self.transmitting_started == -1:
            return Data.NULL
        if (time - self.transmitting_started) % self.signal_time != 0:
            return Data.ZERO
        if disconnected:
            data = Data.NULL
        else:
            pointer = self.data_pointer
            if len(self.data) > 0 and pointer < len(self.data[0]):
                data = Data.ONE if self.data[0][pointer] == 1 else Data.ZERO
                self.data_pointer += 1
            else:
                data = Data.NULL
                self.data.pop(0)
                self.data_pointer = 0
                if len(self.data) < 1:
                    self.transmitting_started = -1
                    self.data = []
                    self.data_pointer = 0
                    self.resend_attempts = 0
                    self.ports[0].data = Data.NULL
        self.send_bit(time, data, disconnected)
        if self.ports[0].device is None:
            self.data_pointer -= 1  # Comment if the the host must not wait to resend data in case of disconnection
            self.resend_attempts += 1
            if self.resend_attempts == 25:
                self.reset()
        elif self.data_pointer > 0:
            self.resend_attempts = 0
        return data if not disconnected and len(self.data) < 1 else data.ZERO

    def set_mac(self, interface: int, mac: str):
        if interface != 0:
            print("\nWRONG MAC INTERFACE.")
            raise Exception
        if mac == "FFFF":
            print("\nWRONG MAC ADDRESS.")
            raise Exception
        self.mac = mac

    def set_ip(self, time: int, interface: int, ip: tuple, mask: tuple):
        if interface != 0:
            print("\nWRONG IP INTERFACE.")
            raise Exception
        if ip[2] == 0 or ip[2] == 255 or ip[3] == 0 or ip[3] == 255:
            print("\nWRONG IP ADDRESS.")
            raise Exception
        for i in range(len(mask)):
            if mask[i] != 255:
                for j in range(i, len(mask)):
                    if mask[i] != 0:
                        print("\nWRONG MASK ADDRESS.")
                        raise Exception
                break
        self.ip = ip
        self.mask = mask
        self.subnet, self.broadcast = self.subnet_broadcast()
        self.table[ip] = self.mac
        if self.ports[0].device is not None:
            self.arpr(time)
