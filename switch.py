from device import Device, Data
from host import Host
from converter import binary_to_decimal, binary_to_hexadecimal


class Switch(Device):
    def __init__(self, signal_time: int, name: str, no_ports: int):
        super().__init__(name, no_ports)
        self.signal_time = signal_time
        self.macs_map = dict()
        self.receiving_data = [[[[] for _ in range(6)]] for _ in range(self.ports_number)]
        self.receiving_data_pointer = [[0, 0, 0] for _ in range(self.ports_number)]
        self.destination_ports = dict()
        self.transmitting_started = [-1 for _ in range(self.ports_number)]
        self.data_pointer = [[0, 0] for _ in range(self.ports_number)]
        self.resend_attempts = [0 for _ in range(self.ports_number)]
        self.origen_ports = [-1 for _ in range(no_ports)]

    def disconnect(self, time: int, port: int):
        if self.destination_ports.keys().__contains__(port) and type(self.ports[port].device) != Host:
            self.receive_bit(time, port, Data.NULL, True)
        disconnected = []
        for key in self.macs_map.keys():
            if self.macs_map[key] == port:
                disconnected.append(key)
        for key in disconnected:
            self.macs_map.pop(key)
        super().disconnect(time, port)

    def receive_bit(self, time: int, port: int, data: Data, disconnected: bool = False):
        super().receive_bit(time, port, data, disconnected)
        self.write("\n")
        receiving_data_pointer = self.receiving_data_pointer[port]
        frame = receiving_data_pointer[0]
        section = receiving_data_pointer[1]
        pointer = receiving_data_pointer[2]
        receiving_data = self.receiving_data[port][frame]
        if data != Data.NULL:
            receiving_data[section].append(1 if data == Data.ONE else 0)
            receiving_data_pointer[2] += 1
            pointer += 1
            if ((section == 0 or section == 1) and pointer == 16) or ((section == 2 or section == 3) and pointer == 8) \
                    or (section == 4 and pointer == binary_to_decimal(receiving_data[2]) * 8) or \
                    (section == 5 and pointer == binary_to_decimal(receiving_data[3]) * 8):
                self.mac_map(time, port, section, receiving_data)
                if section != 5:
                    receiving_data_pointer[1] += 1
                    receiving_data_pointer[2] = 0
                else:
                    self.end_frame(port)
        elif section > 0 or pointer > 0:
            if pointer > 0 and not disconnected:
                self.mac_map(time, port, section, receiving_data)
            self.end_frame(port)

    def mac_map(self, time: int, port: int, section: int, receiving_data: list):
        mac = binary_to_hexadecimal(receiving_data[section])
        if len(mac) != 4:
            return
        if section == 0:
            self.destination(time, port, mac)
        elif section == 1 and mac != "FFFF":
            self.macs_map[mac] = port

    def destination(self, time, port, mac):
        if self.transmitting_started[port] == -1:
            self.transmitting_started[port] = time
        ports = []
        try:
            p = self.ports[self.macs_map[mac]]
            for i in range(self.ports_number):
                if p == self.ports[i]:
                    ports = [(i, p)]
                    break
        except Exception:
            for i in range(self.ports_number):
                if i != port:
                    ports.append((i, self.ports[i]))
        try:
            self.destination_ports[port].append(ports)
        except Exception:
            self.destination_ports[port] = [ports]

    def end_frame(self, port: int):
        self.receiving_data[port].append([[] for _ in range(6)])
        self.receiving_data_pointer[port][0] += 1
        self.receiving_data_pointer[port][1] = 0
        self.receiving_data_pointer[port][2] = 0

    def send(self, time: int):
        sent = False
        for port in range(len(self.ports)):
            if self.send_port(time, port):
                sent = True
        return sent

    def send_port(self, time: int, port: int):
        if self.transmitting_started[port] == -1:
            return False
        if (time - self.transmitting_started[port]) % self.signal_time != 0:
            return True
        ended = False
        receiving_data = self.receiving_data[port]
        pointer = self.data_pointer[port]
        destination_ports = self.destination_ports[port][0]
        if pointer[0] >= len(receiving_data[0]) or len(receiving_data[0][pointer[0]]) < 1:
            ended = True
            data = None
        else:
            data = receiving_data[0][pointer[0]][pointer[1]]
            pointer[1] += 1
            if pointer[1] >= len(receiving_data[0][pointer[0]]):
                pointer[0] += 1
                pointer[1] = 0
        sent = False
        data_string = "null, cause=data_ended" if data is None else data
        self.write("time={}, port={}, send={}\n".format(time, port + 1, data_string))
        for d in destination_ports:
            p = d[0]
            origen_ports = self.origen_ports[p]
            string = "time={}, port={}, resend={}, transmission=".format(time, p + 1, data_string)
            if origen_ports == -1 or origen_ports == port:
                self.origen_ports[p] = port
                cable = d[1]
                cable.data = Data.NULL if data is None else Data.ZERO if data == 0 else Data.ONE
                device = cable.device
                if device is None:
                    self.write("{}incomplete, cause=not_connected\n".format(string))
                else:
                    if device.sending_collision(cable.port):
                        self.collision(string)
                    else:
                        self.write("{}successfully\n".format(string))
                        device.receive_bit(time, cable.port, cable.data, False)
                        sent = True
        self.write("\n")
        self.reset(port, pointer, sent, ended)
        return True

    def reset(self, port, pointer, sent, ended):
        receiving_data_pointer = self.receiving_data_pointer[port]
        if not sent:
            # Comment if the the switch must not wait to resend data in case of collision or disconnection
            if pointer[1] > 0:
                pointer[1] -= 1
            self.resend_attempts[port] += 1
            if self.resend_attempts[port] >= 50:
                ended = receiving_data_pointer[0] > 0 or (receiving_data_pointer[1] < 1 and
                                                          receiving_data_pointer[2] < 1)
        if ended:
            self.receiving_data[port].pop(0)
            if receiving_data_pointer[0] > 0:
                receiving_data_pointer[0] -= 1
            if receiving_data_pointer[1] < 1:
                self.transmitting_started[port] = -1
            self.resend_attempts[port] = 0
            pointer[0] = 0
            pointer[1] = 0
            destination_ports = self.destination_ports[port].pop(0)
            for d in destination_ports:
                d[1].data = Data.NULL
            for i in range(len(self.origen_ports)):
                if self.origen_ports[i] == port:
                    self.origen_ports[i] = -1
