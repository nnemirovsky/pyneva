import serial
from .types import *
from . import tools


class Meter:
    """
    Custom library for working with electricity meters Neva MT 3xx via serial port.
    """

    BAUDRATES = (300, 600, 1200, 2400, 4800, 9600)
    __init_baudrate = BAUDRATES[0]
    __timeout = 3
    __serial_num = None
    __used_tariff_schedules = set()

    def __init__(self, port):
        self.__port = port
        self.__start_session()

    def __start_session(self):
        """
        Starting serial session, sending initial commands.
        """

        self.session = serial.Serial(port=self.__port,
                                     baudrate=self.__init_baudrate,
                                     bytesize=serial.SEVENBITS,
                                     parity=serial.PARITY_EVEN,
                                     stopbits=serial.STOPBITS_ONE,
                                     timeout=self.__timeout)

        self.send_request(tools.Commands.transfer_request)

        try:
            resp = self.get_response(21)
            working_baudrate_num = int(chr(resp[4]))
            self.__working_baudrate = self.BAUDRATES[working_baudrate_num]
            self.__device_name = resp[5:-2].decode("ascii")
        except IndexError:
            raise ConnectionError("identity message format is wrong") from None

        self.send_request(tools.Commands.ack % working_baudrate_num)

        # Flushing data before closing port
        self.session.flush()

        # Reopen port with new baudrate
        self.disconnect()
        self.session.baudrate = self.__working_baudrate
        self.connect()

        try:
            self.__password = tools.parse_response(self.get_response(16)).encode()
        except ValueError:
            raise ConnectionError("password message format is wrong, try again") from None

        self.send_request(tools.make_request(mode="P", data=self.__password))

        msg = self.get_response(1)
        if msg != b"\x06":
            raise ConnectionError(f"message is not ACK, message: {msg}")

    @property
    def total_energy(self) -> TotalEnergy:
        """
        Returns сumulative active energy in tariffs T1, T2, T3, T4 and total [kWh].
        """

        self.send_request(tools.Commands.total_energy)
        return TotalEnergy(*tools.parse_response(self.get_response(62)))

    @property
    def voltage_a(self) -> float:
        """Returns instantaneous voltage in phase A (L1) [V]."""

        self.send_request(tools.Commands.voltage_A)
        return tools.parse_response(self.get_response(20))

    @property
    def voltage_b(self) -> float:
        """Returns instantaneous voltage in phase B (L2) [V]."""

        self.send_request(tools.Commands.voltage_B)
        return tools.parse_response(self.get_response(20))

    @property
    def voltage_c(self) -> float:
        """Returns instantaneous voltage in phase C (L3) [V]."""

        self.send_request(tools.Commands.voltage_C)
        return tools.parse_response(self.get_response(20))

    @property
    def voltage(self) -> Voltage:
        """Returns instantaneous voltages of all phases [V]."""

        return Voltage(phaseA=self.voltage_a, phaseB=self.voltage_b, phaseC=self.voltage_c)

    @property
    def active_power_a(self) -> float:
        """Returns active instantaneous power in phase A (L1) [W]."""

        self.send_request(tools.Commands.active_power_A)
        return tools.parse_response(self.get_response(20))

    @property
    def active_power_b(self) -> float:
        """Returns active instantaneous power in phase B (L2) [W]."""

        self.send_request(tools.Commands.active_power_B)
        return tools.parse_response(self.get_response(20))

    @property
    def active_power_c(self) -> float:
        """Returns active instantaneous power in phase C (L3) [W]."""

        self.send_request(tools.Commands.active_power_C)
        return tools.parse_response(self.get_response(20))

    @property
    def active_power_sum(self) -> float:
        """Returns sum of active instantaneous power of all phases [W]."""

        self.send_request(tools.Commands.active_power_sum)
        return tools.parse_response(self.get_response(20))

    @property
    def active_power(self) -> ActivePower:
        """
        Returns active instantaneous power of all phases and their sum [W].
        """

        return ActivePower(sum=self.active_power_sum,
                           phaseA=self.active_power_a,
                           phaseB=self.active_power_b,
                           phaseC=self.active_power_c)

    @property
    def season_schedule(self) -> tuple[SeasonSchedule, ...]:
        self.send_request(tools.Commands.season_schedule)
        zones = tools.parse_response(self.get_response(144))
        zones_parsed = []
        for zone in zones:
            if zone == "0000000000":
                continue
            zone = tuple(int(zone[i:i + 2]) for i in range(0, len(zone), 2))
            self.__used_tariff_schedules.update(zone[2:])
            zones_parsed.append(SeasonSchedule(*zone))
        return tuple(zones_parsed)

    @property
    def special_days_schedule(self) -> tuple[SpecialDaysSchedule, ...]:
        self.send_request(tools.Commands.special_days)
        days = tools.parse_response(self.get_response(236))
        days_parsed = []
        for day in days:
            if day == "000000":
                continue
            day = tuple([int(day[:2]), int(day[2:4]), int(day[4:])])
            self.__used_tariff_schedules.add(day[-1])
            days_parsed.append(SpecialDaysSchedule(*days))
        return tuple(days_parsed)

    @property
    def tariff_schedules(self) -> tuple[TariffSchedule, ...]:
        tariff_schedules = []
        if not self.__used_tariff_schedules:
            self.__used_tariff_schedules.add(1)
        for schedule_num in self.__used_tariff_schedules:
            obis_cmd = tools.Commands.tariff_schedule_cmd % f"{schedule_num:02X}"
            self.send_request(tools.make_request(obis_cmd))
            resp = self.get_response(68)
            schedule = tools.parse_response(resp)
            schedule_parsed = []
            for part in schedule:
                if part == "000000":
                    break
                # part = tuple(int(part[i:i + 2]) for i in range(0, len(part), 2))
                part = tuple([int(part[:2]), int(part[2:4]), int(part[4:])])
                schedule_parsed.append(TariffSchedulePart(*part))
            if schedule_parsed:
                tariff_schedules.append(TariffSchedule(tuple(schedule_parsed)))
        return tuple(tariff_schedules)

    @property
    def status(self) -> Status:
        self.send_request(tools.Commands.status)
        response = tools.parse_response(self.get_response(17))
        bits = f'{int(response, 16):0>16b}'
        bits = bits[:8] + bits[9:12]
        return Status(*map(lambda x: x == "1", bits))

    @property
    def serial_number(self) -> str:
        if self.__serial_num:
            return self.__serial_num
        self.send_request(tools.Commands.serial_num)
        self.__serial_num = tools.parse_response(self.get_response(21))
        return self.__serial_num

    @property
    def device_name(self) -> str:
        return self.__device_name

    def send_request(self, request: bytes):
        self.session.write(request)

    def get_response(self, size: int = None, expected: bytes = b"\x03") -> bytes:
        """
        Returns raw bytes response from serial port.
        Without args (by default) it reads up to expected ETX char (\x03).
        if size was specified it reads size bytes.
        if expected == None read all before timeout.
        """

        if size:
            return self.session.read(size)
        if expected:
            return self.session.read_until(expected)
        return self.session.readall()

    def disconnect(self):
        self.session.close()

    def connect(self):
        self.session.open()

    def close_session(self):
        self.send_request(tools.Commands.end_conn)
        self.session.flush()
        self.session.close()
        self.session.__del__()

    def __str__(self) -> str:
        return self.device_name

    def __repr__(self) -> str:
        return f"Meter({self.__port!r})"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_session()
