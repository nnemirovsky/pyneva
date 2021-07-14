from typing import Dict, Literal, Tuple, Union
import serial
import re


class Meter:
    """
    SDK for working with electricity meters Neva MT 3xx via serial port.
    """

    password = b""
    serial_num = ""
    device_name = ""
    working_baudrate = 9600
    init_baudrate = 300

    def __init__(self, port):
        self.port = port
        self.commands = {
            # /?!<CR><LF>
            "transfer_request": b"/?!\r\n",
            # <ACK>051<CR><LF>
            "ack": b"\x06051\r\n",
            "total_energy": self.make_request("0F.08.80*FF"),
            "voltage_phase1": self.make_request("20.07.00*FF"),
            "voltage_phase2": self.make_request("34.07.00*FF"),
            "voltage_phase3": self.make_request("48.07.00*FF"),
            "active_power_phase1": self.make_request("24.07.00*FF"),
            "active_power_phase2": self.make_request("38.07.00*FF"),
            "active_power_phase3": self.make_request("4C.07.00*FF"),
            "active_power_phase_sum": self.make_request("10.07.00*FF"),
            "serial_num": self.make_request("60.01.00*FF"),
            "status": self.make_request("60.05.00*FF"),
        }
        self.__start_session()

    def __start_session(self):
        """
        Starting serial session, sending initial commands.
        """

        self.session = serial.Serial(self.port,
                                     self.init_baudrate,
                                     serial.SEVENBITS,
                                     serial.PARITY_EVEN,
                                     timeout=2)

        self.send_request(self.commands["transfer_request"])

        try:
            self.device_name = self.get_response()[5:-2].decode("ascii")
        except IndexError:
            raise ConnectionError("Identity message format is wrong") from None

        self.send_request(self.commands["ack"])
        self.disconnect()

        # Reopen port with new baudrate
        self.session.baudrate = self.working_baudrate
        self.connect()

        try:
            self.password = self.parse_response(self.get_response()).encode()
        except ValueError:
            raise ConnectionError("Password message format is wrong") from None

        self.send_request(self.make_request(mode="P", data=self.password))

        msg = self.get_response()
        if msg != b"\x06":
            raise ConnectionError(f"Message is not ACK, message: {msg}")

    def get_total_energy(self) -> tuple[float]:
        """
        Returns accumulated active energy.
        """

        self.send_request(self.commands["total_energy"])
        return self.parse_response(self.get_response())

    def get_phase_voltages(self) -> tuple[float]:
        """
        Returns current voltage of all phases.
        """

        self.send_request(self.commands["voltage_phase1"])
        v1 = self.parse_response(self.get_response())

        self.send_request(self.commands["voltage_phase2"])
        v2 = self.parse_response(self.get_response())

        self.send_request(self.commands["voltage_phase3"])
        v3 = self.parse_response(self.get_response())

        return v1, v2, v3

    def get_active_power(self) -> tuple[float]:
        """
        Returns current active power (in watts) of all phases.
        """

        self.send_request(self.commands["active_power_phase_sum"])
        w_sum = self.parse_response(self.get_response())

        self.send_request(self.commands["active_power_phase1"])
        w1 = self.parse_response(self.get_response())

        self.send_request(self.commands["active_power_phase2"])
        w2 = self.parse_response(self.get_response())

        self.send_request(self.commands["active_power_phase3"])
        w3 = self.parse_response(self.get_response())

        return w_sum, w1, w2, w3

    def get_serial_number(self) -> int:
        if self.serial_num:
            return self.serial_num
        self.send_request(self.commands["serial_num"])
        self.serial_num = self.parse_response(self.get_response())
        return self.serial_num

    def get_status(self) -> Dict[str, bool]:
        self.send_request(self.commands["status"])
        response = self.parse_response(self.get_response())
        bits = f'{int(response, 16):0>16b}'
        bits = bits[:8] + bits[9:12]
        status = {
            "data_memory_err": 0,
            "param_memory_err": 0,
            "measurement_err": 0,
            "clock_err": 0,
            "battery_discharged": 0,
            "programming_button_pressed": 0,
            "data_memory_doesnt_work": 0,
            "param_memory_doesnt_work": 0,
            "screw_terminal_cover_removed": 0,
            "load_connected": 0,
            "load_disconnected": 0
        }
        keys = list(status)
        for k, v in enumerate(bits):
            status[keys[k]] = v == "1"

        return status

    def make_request(self,
                     obis: str = "",
                     mode: Literal["P", "W", "R"] = "R",
                     data: bytes = b"") -> bytes:

        if type(obis) != str:
            raise TypeError(f"OBIS must be str, not {type(obis).__name__}")

        if mode not in ("P", "W", "R"):
            raise ValueError(f"mode must be in ('P', 'W', 'R'), not '{mode}'")

        if mode in ("P", "W") and not data:
            raise ValueError("data cannot be empty if mode in ('P', 'W')")

        if obis and mode == "P":
            raise ValueError("mode cannot be 'P' if OBIS code was provided")

        if obis:
            pattern = re.compile(r"[A-F0-9]{2}\.[A-F0-9]{2}\.[A-F0-9]{2}\*FF")
            if not bool(pattern.fullmatch(obis)):
                raise ValueError("OBIS code format is wrong")
            obis = obis[:2] + obis[3:5] + obis[6:8] + obis[9:]

        obis = obis.encode()
        data = b"(%s)" % data

        request = b"\x01" + mode.encode() + b"1\x02" + obis + data + b"\x03"
        request += self.calculate_bcc(request[1:])

        return request

    def parse_response(
            self,
            response: bytes) -> Union[str, float, Tuple[Union[str, float]]]:
        try:
            bracket_idx = response.index(b"(")
            response = response[bracket_idx + 1:-3]
        except (IndexError, ValueError):
            raise ValueError(
                f"Invalid response format, response: {response}") from None

        response = response.split(b",")
        if b"." in response[0]:
            if len(response) != 1:
                return tuple(map(float, response))
            return float(response[0])
        if len(response) != 1:
            return tuple(map(lambda x: x.decode("ascii"), response))
        return response[0].decode("ascii")

    def send_request(self, request: bytes):
        self.session.write(request)

    def get_response(self) -> bytes:
        return self.session.readall()

    def disconnect(self):
        self.session.close()

    def connect(self):
        self.session.open()

    def calculate_bcc(self, data: bytes) -> bytes:
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bcc.to_bytes(1, "little")

    def __str__(self) -> str:
        return self.device_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()
