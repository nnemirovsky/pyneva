from collections import namedtuple
from typing import Literal, Tuple, Union
import time
import serial
import re


class Meter:
    """
    Custom library for working with electricity meters Neva MT 3xx via serial port.
    """

    BAUDRATES = (300, 600, 1200, 2400, 4800, 9600)
    __serial_num = None
    __init_baudrate = BAUDRATES[0]
    __timeout = 3
    __used_tariff_schedules = set()

    Status = namedtuple("Status",
                        ("data_memory_err", "param_memory_err", "measurement_err", "clock_err",
                         "battery_discharged", "programming_button_pressed",
                         "data_memory_doesnt_work", "param_memory_doesnt_work",
                         "screw_terminal_cover_removed", "load_connected", "load_disconnected"))
    TotalEnergy = namedtuple("TotalEnergy", "sum T1 T2 T3 T4")
    Voltage = namedtuple("Voltage", "phase1 phase2 phase3")
    Amperage = namedtuple("Amperage", "sum phase1 phase2 phase3")
    SeasonSchedule = namedtuple("SeasonSchedule", "month day weekday_skd sat_skd sun_skd")
    SpecialDaysSchedule = namedtuple("SpecialDaysSchedule", "month day skd")
    TariffSchedulePart = namedtuple("TariffSchedulePart", "hour minute T_num")
    TariffSchedule = namedtuple("TariffSchedule", "parts")

    def __init__(self, port):
        self.port = port
        self.commands = {
            # /?!<CR><LF>
            "transfer_request": b"/?!\r\n",
            # <ACK>051<CR><LF>
            "ack": b"\x060%i1\r\n",
            # <SOH>B0<ETX><bcc>
            "end_conn": b"\x01B0\x03q",
            "total_energy": self.make_request("0F.08.80*FF"),
            "voltage_phase1": self.make_request("20.07.00*FF"),
            "voltage_phase2": self.make_request("34.07.00*FF"),
            "voltage_phase3": self.make_request("48.07.00*FF"),
            "amperage_phase1": self.make_request("24.07.00*FF"),
            "amperage_phase2": self.make_request("38.07.00*FF"),
            "amperage_phase3": self.make_request("4C.07.00*FF"),
            "amperage_sum": self.make_request("10.07.00*FF"),
            "serial_num": self.make_request("60.01.00*FF"),
            "status": self.make_request("60.05.00*FF"),
            "season_schedule": self.make_request("0D.00.00*FF"),
            "special_days": self.make_request("0B.00.00*FF"),
            "tariff_schedule_cmd": "0A.%s.64*FF",
        }
        self.__start_session()

    def __start_session(self):
        """
        Starting serial session, sending initial commands.
        """

        self.session = serial.Serial(port=self.port,
                                     baudrate=self.__init_baudrate,
                                     bytesize=serial.SEVENBITS,
                                     parity=serial.PARITY_EVEN,
                                     stopbits=serial.STOPBITS_ONE,
                                     timeout=self.__timeout)

        self.send_request(self.commands["transfer_request"])

        try:
            resp = self.get_response(21)
            working_baudrate_num = int(chr(resp[4]))
            self.__working_baudrate = self.BAUDRATES[working_baudrate_num]
            self.__device_name = resp[5:-2].decode("ascii")
        except IndexError:
            raise ConnectionError("Identity message format is wrong") from None

        self.send_request(self.commands["ack"] % working_baudrate_num)

        time.sleep(.5)
        self.session.flush()
        # Change baudrate
        self.session.baudrate = self.__working_baudrate

        try:
            self.__password = self.parse_response(self.get_response(16)).encode()
        except ValueError:
            raise ConnectionError("Password message format is wrong, try again") from None

        self.send_request(self.make_request(mode="P", data=self.__password))

        msg = self.get_response(1)
        if msg != b"\x06":
            raise ConnectionError(f"Message is not ACK, message: {msg}")

    @property
    def total_energy(self) -> TotalEnergy:
        """
        Returns accumulated active energy.
        """

        resp_size = 62

        self.send_request(self.commands["total_energy"])
        return self.TotalEnergy(*self.parse_response(self.get_response(resp_size)))

    @property
    def voltage(self) -> Voltage:
        """
        Returns current voltage of all phases.
        """

        resp_size = 20

        self.send_request(self.commands["voltage_phase1"])
        v1 = self.parse_response(self.get_response(resp_size))

        self.send_request(self.commands["voltage_phase2"])
        v2 = self.parse_response(self.get_response(resp_size))

        self.send_request(self.commands["voltage_phase3"])
        v3 = self.parse_response(self.get_response(resp_size))

        return self.Voltage(phase1=v1, phase2=v2, phase3=v3)

    @property
    def amperage(self) -> Amperage:
        """
        Returns current active power (in watts) of all phases.
        """

        resp_size = 20

        self.send_request(self.commands["amperage_sum"])
        w_sum = self.parse_response(self.get_response(resp_size))

        self.send_request(self.commands["amperage_phase1"])
        w1 = self.parse_response(self.get_response(resp_size))

        self.send_request(self.commands["amperage_phase2"])
        w2 = self.parse_response(self.get_response(resp_size))

        self.send_request(self.commands["amperage_phase3"])
        w3 = self.parse_response(self.get_response(resp_size))

        return self.Amperage(sum=w_sum, phase1=w1, phase2=w2, phase3=w3)

    @property
    def season_schedule(self) -> Tuple[SeasonSchedule, ...]:
        self.send_request(self.commands["season_schedule"])
        zones = self.parse_response(self.get_response(144))
        zones_parsed = []
        for zone in zones:
            if zone == "0000000000":
                continue
            zone = tuple(int(zone[i:i + 2]) for i in range(0, len(zone), 2))
            self.__used_tariff_schedules.update(zone[2:])
            zones_parsed.append(self.SeasonSchedule(*zone))
        return tuple(zones_parsed)

    @property
    def special_days_schedule(self) -> Tuple[SpecialDaysSchedule, ...]:
        self.send_request(self.commands["special_days"])
        days = self.parse_response(self.get_response(236))
        days_parsed = []
        for day in days:
            if day == "000000":
                continue
            day = tuple([int(day[:2]), int(day[2:4]), int(day[4:])])
            self.__used_tariff_schedules.add(day[-1])
            days_parsed.append(self.SpecialDaysSchedule(*days))
        return tuple(days_parsed)

    @property
    def tariff_schedules(self) -> Tuple[TariffSchedule, ...]:
        tariff_schedules = []
        if not self.__used_tariff_schedules:
            self.__used_tariff_schedules.add(1)
        for schedule_num in self.__used_tariff_schedules:
            obis_cmd = self.commands["tariff_schedule_cmd"] % f"{schedule_num:02X}"
            self.send_request(self.make_request(obis_cmd))
            resp = self.get_response(68)
            schedule = self.parse_response(resp)
            schedule_parsed = []
            for part in schedule:
                if part == "000000":
                    break
                # part = tuple(int(part[i:i + 2]) for i in range(0, len(part), 2))
                part = tuple([int(part[:2]), int(part[2:4]), int(part[4:])])
                schedule_parsed.append(self.TariffSchedulePart(*part))
            if schedule_parsed:
                tariff_schedules.append(self.TariffSchedule(tuple(schedule_parsed)))
        return tuple(tariff_schedules)

    @property
    def serial_number(self) -> str:
        if self.__serial_num:
            return self.__serial_num
        self.send_request(self.commands["serial_num"])
        self.__serial_num = self.parse_response(self.get_response(21))
        return self.__serial_num

    @property
    def device_name(self) -> str:
        return self.__device_name

    @property
    def status(self) -> Status:
        self.send_request(self.commands["status"])
        response = self.parse_response(self.get_response(17))
        bits = f'{int(response, 16):0>16b}'
        bits = bits[:8] + bits[9:12]
        return self.Status(*map(lambda x: x == "1", bits))

    def make_request(self, obis: str = "", mode: Literal["P", "W", "R"] = "R",
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

    def parse_response(self, response: bytes) -> Union[str, float, Tuple[Union[str, float], ...]]:
        try:
            bracket_idx = response.index(b"(")
            response = response[bracket_idx + 1:-3]
        except (IndexError, ValueError):
            raise ValueError(f"Invalid response format, response: {response}") from None

        response = response.split(b",")
        if b"." in response[0]:
            if len(response) != 1:
                return tuple(map(float, response))
            return float(response[0])
        if len(response) != 1:
            return tuple(map(lambda x: x.decode("ascii"), response))
        return response[0].decode("ascii")

    def calculate_bcc(self, data: bytes) -> bytes:
        bcc = 0
        for byte in data:
            bcc ^= byte
        return bcc.to_bytes(1, "little")

    def send_request(self, request: bytes):
        self.session.write(request)

    def get_response(self, size: int = None) -> bytes:
        if size:
            return self.session.read(size)
        return self.session.readall()

    def disconnect(self):
        self.session.close()

    def connect(self):
        self.session.open()

    def close_session(self):
        self.send_request(self.commands["end_conn"])
        self.session.flush()
        self.session.close()
        self.session.__del__()

    def __str__(self) -> str:
        return self.device_name

    def __repr__(self) -> str:
        return f"Meter({self.port!r})"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_session()
