from hub import Hub
from host import Host
from switch import Switch
from converter import hexadecimal_to_binary


class Layer:
    def __init__(self, signal_time: int, error_detection: str):
        self.signal_time = signal_time
        self.error_detection = error_detection
        self.devices = set()
        self.macs = set()
        self.ips = set()

    def create(self, device: str, name: str, ports_number: int = 1):
        if device == "hub":
            self.devices.add(Hub(name, ports_number))
        elif device == "host":
            self.devices.add(Host(self.signal_time, self.error_detection, name))
        elif device == "switch":
            self.devices.add(Switch(self.signal_time, name, ports_number))

    def connect(self, time: int, device1: str, port1: int, device2: str, port2: int):
        if device1 == device2:
            print("\nCAN'T CONNECT A DEVICE WITH ITSELF.")
            raise Exception
        d1 = None
        d2 = None
        for d in self.devices:
            if d.name == device1:
                d1 = d
            elif d.name == device2:
                d2 = d
        if d1 is None or d2 is None:
            print("\nUNRECOGNIZED DEVICE.")
            raise Exception
        if port1 > d1.ports_number or port2 > d2.ports_number:
            print("\nUNRECOGNIZED PORT.")
            raise Exception
        d1.connect(time, port1, d2, port2)
        d2.connect(time, port2, d1, port1)

    def send(self, time: int, host: str, data: list):
        for d in self.devices:
            if d.name == host:
                if type(d) != Host:
                    print("\nWRONG SEND INSTRUCTION DEVICE TYPE.")
                    raise Exception
                if len(data) % 8 != 0:
                    print("\nDATA ISN'T A MULTIPLE OF 8.")
                    raise Exception
                d.start_send(time, data)
                return
        print("\nUNRECOGNIZED DEVICE.")
        raise Exception

    def disconnect(self, time: int, device: str, port: int):
        for d in self.devices:
            if d.name == device:
                if port > d.ports_number:
                    print("\nUNRECOGNIZED PORT.")
                    raise Exception
                d.disconnect(time, port)
                return
        print("\nUNRECOGNIZED DEVICE.")
        raise Exception

    def mac(self, host: str, address: str):
        for d in self.devices:
            if d.name == host:
                if type(d) != Host:
                    print("\nWRONG MAC INSTRUCTION DEVICE TYPE.")
                    raise Exception
                try:
                    int(address, 16)
                except Exception:
                    print("\nMAC ISN'T HEXADECIMAL.")
                    raise Exception
                count = len(self.macs)
                self.macs.add(address)
                if count == len(self.macs):
                    print("\nMAC ALREADY USED.")
                    raise Exception
                d.set_mac(address)
                return
        print("\nUNRECOGNIZED DEVICE.")
        raise Exception

    def send_frame(self, time: int, host: str, destination_mac: str, data: str):
        for d in self.devices:
            if d.name == host:
                if type(d) != Host:
                    print("\nWRONG SEND FRAME INSTRUCTION DEVICE TYPE.")
                    raise Exception
                try:
                    destination_mac = hexadecimal_to_binary(destination_mac)
                except Exception:
                    print("\nMAC ISN'T HEXADECIMAL.")
                    raise Exception
                try:
                    data = hexadecimal_to_binary(data)
                except Exception:
                    print("\nDATA ISN'T HEXADECIMAL.")
                    raise Exception
                if len(data) % 8 != 0:
                    print("\nDATA ISN'T A MULTIPLE OF 8.")
                    raise Exception
                d.start_send(time, data, destination_mac)
                return
        print("\nUNRECOGNIZED DEVICE.")
        raise Exception

    def ip(self, time: int, host: str, address: str):
        for d in self.devices:
            if d.name == host:
                if type(d) != Host:
                    print("\nWRONG IP INSTRUCTION DEVICE TYPE.")
                    raise Exception
                count = len(self.ips)
                self.ips.add(address)
                if count == len(self.ips):
                    print("\nIP ALREADY USED.")
                    raise Exception
                d.set_ip(time, self.get_ip(address))
                return
        print("\nUNRECOGNIZED DEVICE.")
        raise Exception

    @staticmethod
    def get_ip(ip: str):
        ip = ip.split('.')
        if len(ip) != 4:
            print("\nWRONG IP FORMAT.")
            raise Exception
        try:
            ip = tuple([int(x) for x in ip])
        except Exception:
            print("\nIP ISN'T DECIMAL.")
            raise Exception
        for i in ip:
            if i < 0 or i > 255:
                print("\nWRONG IP VALUE.")
                raise Exception
        return ip

    def send_packet(self, time: int, host: str, destination_ip: str, data: str):
        for d in self.devices:
            if d.name == host:
                if type(d) != Host:
                    print("\nWRONG SEND PACKET INSTRUCTION DEVICE TYPE.")
                    raise Exception
                try:
                    data = hexadecimal_to_binary(data)
                except Exception:
                    print("\nDATA ISN'T HEXADECIMAL.")
                    raise Exception
                if len(data) % 8 != 0:
                    print("\nDATA ISN'T A MULTIPLE OF 8.")
                    raise Exception
                d.packet(time, data, self.get_ip(destination_ip))
                return
        print("\nUNRECOGNIZED DEVICE.")
        raise Exception
