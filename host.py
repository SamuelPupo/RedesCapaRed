from hub import Device, Data
from algorithms import define, create, detect
from converter import binary_to_hexadecimal, binary_to_decimal, hexadecimal_to_binary, decimal_to_binary


class Host(Device):
    def __init__(self, signal_time: int, error_detection: str, name: str, mac: str = "FFFF", ip: tuple = None):
        super().__init__(name, 1)
        self.signal_time = signal_time
        self.error_detection = define(str.upper(error_detection))
        self.mac = mac
        self.ip = ip
        self.table = dict()
        self.transmitting_started = -1
        self.data = []
        self.data_pointer = [0, 0]
        self.resend_attempts = 0
        self.waiting_packet = []
        self.arpq = [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0]
        self.receiving_data = [[] for _ in range(6)]
        self.receiving_data_pointer = [0, 0]
        self.arpr = [0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1]
        file = open("output/{}_data.txt".format(name), 'w')
        file.close()
        file = open("output/{}_payload.txt".format(name), 'w')
        file.close()

    def connect(self, time: int, port: int, other_device, other_port: int):
        super().connect(time, port, other_device, other_port)
        if self.ports[0].data != Data.NULL:
            self.data_pointer[1] += 1

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
        self.data_pointer[1] = 0  # Comment if the the host must not restart sending data in case of disconnection

    def collision(self, string: str):
        super().collision(string)
        if self.data_pointer[1] > 0:
            self.data_pointer[1] -= 1  # Comment if the the host must not wait to resend data in case of collision
        self.resend_attempts += 1
        if self.resend_attempts == 50:
            self.reset()

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

    def reset_receiving(self, time):
        destination = self.receiving_data[0]
        if destination == self.mac or destination == "FFFF":
            sender = self.receiving_data[1]
            data = self.receiving_data[4]
            state = "ERROR" if self.receiving_data[2] != len(self.receiving_data[4]) or \
                self.receiving_data[3] != len(self.receiving_data[5]) or \
                not detect(self.error_detection, self.receiving_data[4], self.receiving_data[5]) else "OK"
            if len(data) == 64:
                arp = data[:32]
                ip = data[32:]
                ip = (binary_to_decimal(ip[:8]), binary_to_decimal(ip[8:16]), binary_to_decimal(ip[16:24]),
                      binary_to_decimal(ip[24:]))
                origen_ip = "NULL"
                action = ""
                if self.arpq == arp:
                    if self.ip == ip:
                        action = "ARPQ"
                        self.arp(time, hexadecimal_to_binary(str(sender)))
                elif self.arpr == arp:
                    self.table[tuple(ip)] = sender
                    origen_ip = "{}.{}.{}.{}".format(ip[0], ip[1], ip[2], ip[3])
                    action = "ARPR"
                    for p in self.waiting_packet:
                        if p[0] == ip:
                            self.packet(time, p[1], ip)
                            break
                if len(action) > 0:
                    file = open("output/{}_payload.txt".format(self.name), 'a')
                    file.write("time={}, host_ip={}, action={}\n".format(time, origen_ip, action))
                    file.close()
            else:
                if len(data) >= 88:
                    destination_ip = data[:32]
                    destination_ip = (binary_to_decimal(destination_ip[:8]), binary_to_decimal(destination_ip[8:16]),
                                      binary_to_decimal(destination_ip[16:24]), binary_to_decimal(destination_ip[24:]))
                    origen_ip = data[32:64]
                    origen_ip = (binary_to_decimal(origen_ip[:8]), binary_to_decimal(origen_ip[8:16]),
                                 binary_to_decimal(origen_ip[16:24]), binary_to_decimal(origen_ip[24:]))
                    # ttl = data[64:72]
                    # protocol = data[72:80]
                    length = binary_to_decimal(data[80:88]) * 8
                    packet_data = data[88:]
                    if self.ip == destination_ip:
                        file = open("output/{}_payload.txt".format(self.name), 'a')
                        origen_ip = "{}.{}.{}.{}".format(origen_ip[0], origen_ip[1], origen_ip[2], origen_ip[3])
                        packet_data = binary_to_hexadecimal(packet_data)
                        file.write("time={}, host_ip={}, data={}".format(time, origen_ip,
                                                                         packet_data if len(packet_data) > 0
                                                                         else "NULL"))
                        file.write(", state={}\n".format("ERROR" if length / 4 != len(packet_data) or state == "ERROR"
                                                         else "OK"))
                        file.close()
            file = open("output/{}_data.txt".format(self.name), 'a')
            data = binary_to_hexadecimal(data)
            file.write("time={}, host_mac={}, data={}".format(time, sender if len(sender) > 0 else "FFFF",
                                                              data if len(data) > 0 else "NULL"))
            file.write(", state={}\n".format(state))
            file.close()
        self.receiving_data = [[] for _ in range(6)]
        self.receiving_data_pointer = [0, 0]

    def arp(self, time: int, destination_mac: list = None):
        self.start_send(time, self.arpr + self.binary_ip(), destination_mac)

    def binary_ip(self):
        return decimal_to_binary(self.ip[0]) + decimal_to_binary(self.ip[1]) + decimal_to_binary(self.ip[2]) + \
               decimal_to_binary(self.ip[3])

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
            frame = self.data_pointer[0]
            pointer = self.data_pointer[1]
            if pointer < len(self.data[frame]):
                data = Data.ONE if self.data[frame][pointer] == 1 else Data.ZERO
                self.data_pointer[1] += 1
            else:
                data = Data.NULL
                self.data_pointer[0] += 1
                self.data_pointer[1] = 0
                frame += 1
                if frame >= len(self.data):
                    self.reset()
        self.send_bit(time, data, disconnected)
        if self.ports[0].device is None:
            self.data_pointer[1] -= 1  # Comment if the the host must not wait to resend data in case of disconnection
            self.resend_attempts += 1
            if self.resend_attempts == 25:
                self.reset()
        elif self.data_pointer[1] > 0:
            self.resend_attempts = 0
        return data if not disconnected and len(self.data) < 1 else data.ZERO

    def reset(self):
        self.transmitting_started = -1
        self.data = []
        self.data_pointer = [0, 0]
        self.ports[0].data = Data.NULL

    def set_mac(self, mac: str):
        if mac == "FFFF":
            print("WRONG MAC ADDRESS.")
            raise Exception
        self.mac = mac

    def set_ip(self, time: int, ip: tuple):
        if ip[2] == 0 or ip[2] == 255 or ip[3] == 0 or ip[3] == 255:
            print("WRONG IP ADDRESS.")
            raise Exception
        self.ip = ip
        self.table[self.ip] = self.mac
        if self.ports[0].device is not None:
            self.arp(time)

    def packet(self, time: int, data: list, destination_ip: tuple):
        binary_destination_ip = []
        for x in destination_ip:
            binary_destination_ip += decimal_to_binary(x)
        try:
            destination_mac = hexadecimal_to_binary(self.table[destination_ip])
        except Exception:
            self.waiting_packet.append((destination_ip, data))
            self.start_send(time, self.arpq + binary_destination_ip)
        else:
            origen_ip = self.binary_ip()
            ttl = [0, 0, 0, 0, 0, 0, 0, 0]
            protocol = [0, 0, 0, 0, 0, 0, 0, 0]
            length = decimal_to_binary(int(len(data) / 8))
            self.start_send(time, binary_destination_ip + origen_ip + ttl + protocol + length + data, destination_mac)
