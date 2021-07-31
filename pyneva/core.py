from datetime import datetime
from time import sleep

import serial
from serial.rfc2217 import Serial as rfc2217Serial

from . import tools
from .types import OBISCodes, ResponseError, MeterConnectionError, SeasonalSchedule, \
    SpecialDaysSchedule, TariffSchedule, TariffSchedulePart, Status, TotalEnergy, Voltage, \
    ActivePower


class MeterBase:
    """Base class for working with electricity meters Neva.
    Implements basic methods, excluding those that depend on the meter type.
    """

    __baudrates = (300, 600, 1200, 2400, 4800, 9600)
    __init_baudrate = __baudrates[0]
    __timeout = 3
    __serial_num = None
    __used_tariff_schedules = set()
    OBISCodes = OBISCodes(total_energy="", serial_num="", status="", seasonal_schedules="",
                          special_days_schedules="", tariff_schedule_obis="", date="", address="")

    def __init__(self, interface: str, address: str = "", password: str = ""):
        self.__interface = interface
        self.__address = address
        self.__password = password.encode("ascii")
        self.__session = serial.serial_for_url(self.__interface, baudrate=self.__init_baudrate,
                                               bytesize=serial.SEVENBITS,
                                               parity=serial.PARITY_EVEN,
                                               stopbits=serial.STOPBITS_ONE,
                                               timeout=self.__timeout)
        self.__is_rfc2217 = isinstance(self.__session, rfc2217Serial)
        self.__start_session()

    def __start_session(self):
        """Starting serial session by protocol 61107 in programming mode."""
        # Send request message
        self.send(b"/?%s!\r\n" % self.__address.encode("ascii"))

        # Read identification message
        try:
            msg = tools.parse_id_msg(self.recv(21))
            self.__working_baudrate = self.__baudrates[msg.baudrate_num]
            self.__device_model = msg.ident
        except ResponseError as e:
            self.__session.__del__()
            raise MeterConnectionError(e) from None

        # Send acknowledgement message, programming mode
        self.send(b"\x060%i1\r\n" % msg.baudrate_num)

        # Changing baudrate
        sleep(.3)
        self.__session.baudrate = self.__working_baudrate

        # Read password message
        try:
            resp_size = 15 if self.__is_rfc2217 else 16
            resp = self.recv(resp_size)
            resp = (b"\x01" + resp) if self.__is_rfc2217 else resp
            if not self.__password:
                self.__password = tools.parse_password_msg(resp)
        except ResponseError as e:
            self.__session.__del__()
            raise MeterConnectionError(e)

        # Send password comparison command message
        self.send(tools.make_cmd_msg(mode="P", data=self.__password))

        # Read confirmation message
        if msg := self.recv(1) != b"\x06":
            self.__session.__del__()
            raise MeterConnectionError(f"message is not ACK, message: {msg}")

    @property
    def seasonal_schedules(self) -> tuple[SeasonalSchedule, ...]:
        """
        Returns tuple with seasonal schedules.
        Each schedule specifies from which date the tariff starts,
        and the numbers of tariff schedules on weekdays, Saturdays, Sundays separately.
        """
        self.send(tools.make_cmd_msg(self.OBISCodes.seasonal_schedules))
        seasons = tools.parse_data_msg(self.recv(144)).data
        seasons = tuple(map(lambda skd: SeasonalSchedule(*skd), tools.parse_schedules(seasons)))
        for season in seasons:
            self.__used_tariff_schedules.update(season[2:])
        return seasons

    @property
    def special_days_schedules(self) -> tuple[SpecialDaysSchedule, ...]:
        """
        Returns tuple with special days schedules.
        Each schedule includes date and tariff schedule number.
        """
        self.send(tools.make_cmd_msg(self.OBISCodes.special_days_schedules))
        days = tools.parse_data_msg(self.recv(236)).data
        days = tuple(map(lambda skd: SpecialDaysSchedule(*skd), tools.parse_schedules(days)))
        self.__used_tariff_schedules.update(map(lambda x: x.skd_num, days))
        return days

    @property
    def tariff_schedules(self) -> tuple[TariffSchedule, ...]:
        """
        Returns tuple with tariff schedules.
        Each tariff schedule contains parts of the schedule.
        Each schedule part describes from what time of day the tariff starts,
        and tariff number.
        """
        tariff_schedules = []
        if not self.__used_tariff_schedules:
            self.__used_tariff_schedules.add(1)
        for schedule_num in self.__used_tariff_schedules:
            current_skd_obis = self.OBISCodes.tariff_schedule_obis % f"{schedule_num:02X}"
            self.send(tools.make_cmd_msg(current_skd_obis))
            resp = self.recv(68)
            schedule_part = tools.parse_data_msg(resp).data
            schedule_part = tuple(
                map(lambda skd: TariffSchedulePart(*skd), tools.parse_schedules(schedule_part))
            )
            if schedule_part:
                tariff_schedules.append(TariffSchedule(schedule_part))
        return tuple(tariff_schedules)

    @property
    def date(self) -> datetime.date:
        """Returns current date from the meter."""
        self.send(tools.make_cmd_msg(self.OBISCodes.date))
        date = tools.parse_data_msg(self.recv(19)).data
        return datetime.strptime(date, "%y%m%d").date()

    @property
    def status(self) -> Status:
        """Returns status of meter errors."""
        self.send(tools.make_cmd_msg(self.OBISCodes.status))
        response = tools.parse_data_msg(self.recv(17)).data
        bits = f'{int(response, 16):0>16b}'
        bits = bits[:8] + bits[9:12]
        return Status(*map(lambda x: x == "1", bits))

    @property
    def serial_number(self) -> str:
        """Returns serial number of the meter."""
        if not self.__serial_num:
            self.send(tools.make_cmd_msg(self.OBISCodes.serial_num))
            self.__serial_num = tools.parse_data_msg(self.recv(21)).data
        return self.__serial_num

    @property
    def model(self) -> str:
        """Returns meter name obtained at initialization."""
        return self.__device_model

    @property
    def address(self) -> str:
        """Returns network address of the meter (may be the same as the meter model)."""
        if self.__address:
            return self.__address
        self.send(tools.make_cmd_msg(self.OBISCodes.address))
        self.__address = tools.parse_data_msg(self.recv(21)).data
        return self.__address

    @property
    def temperature(self) -> int:
        """Returns meter temperature."""
        self.send(tools.make_cmd_msg(self.OBISCodes.temperature))
        return int(tools.parse_data_msg(self.recv(16)).data)

    def send(self, message: bytes):
        """Sends sequence of bytes to meter."""
        self.__session.write(message)

    def recv(self, size: int = None, expected: bytes = b"\x03") -> bytes:
        """
        Returns sequence of bytes received from meter.
        Without args (by default) it reads up to expected ETX char.
        If size was specified it reads size bytes.
        If expected == None and size == None and session by RFC2217 protocol
        read all before timeout.
        """
        if (self.__is_rfc2217 or not expected) and not size:
            return self.__session.readall()
        elif size:
            return self.__session.read(size)
        elif expected:
            resp = self.__session.read_until(expected)
            if expected == b"\x03":
                try:
                    resp += expected
                    resp += tools.calculate_bcc(resp[1:])
                except IndexError:
                    raise ResponseError(f"invalid response format, response: {resp}") from None
            self.__session.flushInput()
            return resp

    def __del__(self):
        if self.__session.is_open:
            self.send(b"\x01B0\x03q")
            self.__session.flush()
            self.__session.__del__()

    def __str__(self) -> str:
        return f"[{self.model} : {self.address}]"

    def __repr__(self) -> str:
        return f"Meter({self.__interface!r}, {self.address!r})"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()


class MultiTariffMeter(MeterBase):
    """Base class for multi-tariff meters."""

    @property
    def total_energy(self) -> TotalEnergy:
        """Returns сumulative active energy in tariffs T1, T2, T3, T4 and total [kWh]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.total_energy))
        return TotalEnergy(*tools.parse_data_msg(self.recv(62)).data)


class ThreePhaseMeter(MeterBase):
    """Base class for three-phase meters."""

    @property
    def voltage_a(self) -> float:
        """Returns instantaneous voltage in phase A (L1) [V]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.voltage_A))
        return tools.parse_data_msg(self.recv(20)).data

    @property
    def voltage_b(self) -> float:
        """Returns instantaneous voltage in phase B (L2) [V]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.voltage_B))
        return tools.parse_data_msg(self.recv(20)).data

    @property
    def voltage_c(self) -> float:
        """Returns instantaneous voltage in phase C (L3) [V]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.voltage_C))
        return tools.parse_data_msg(self.recv(20)).data

    @property
    def voltage(self) -> Voltage:
        """Returns instantaneous voltages of all phases [V]."""
        return Voltage(phaseA=self.voltage_a, phaseB=self.voltage_b, phaseC=self.voltage_c)

    @property
    def active_power_a(self) -> float:
        """Returns active instantaneous power in phase A (L1) [W]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.active_power_A))
        return tools.parse_data_msg(self.recv(20)).data

    @property
    def active_power_b(self) -> float:
        """Returns active instantaneous power in phase B (L2) [W]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.active_power_B))
        return tools.parse_data_msg(self.recv(20)).data

    @property
    def active_power_c(self) -> float:
        """Returns active instantaneous power in phase C (L3) [W]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.active_power_C))
        return tools.parse_data_msg(self.recv(20)).data

    @property
    def active_power_sum(self) -> float:
        """Returns sum of active instantaneous power of all phases [W]."""
        self.send(tools.make_cmd_msg(self.OBISCodes.active_power_sum))
        return tools.parse_data_msg(self.recv(20)).data

    @property
    def active_power(self) -> ActivePower:
        """Returns active instantaneous power of all phases and their sum [W]."""
        return ActivePower(sum=self.active_power_sum,
                           phaseA=self.active_power_a,
                           phaseB=self.active_power_b,
                           phaseC=self.active_power_c)


class NevaMT3(MultiTariffMeter, ThreePhaseMeter):
    """Class for working with electricity meters Neva MT 3xx."""

    OBISCodes = OBISCodes(
        total_energy="0F.08.80*FF",
        voltage_A="20.07.00*FF",
        voltage_B="34.07.00*FF",
        voltage_C="48.07.00*FF",
        active_power_A="24.07.00*FF",
        active_power_B="38.07.00*FF",
        active_power_C="4C.07.00*FF",
        active_power_sum="10.07.00*FF",
        serial_num="60.01.00*FF",
        status="60.05.00*FF",
        seasonal_schedules="0D.00.00*FF",
        special_days_schedules="0B.00.00*FF",
        tariff_schedule_obis="0A.%s.64*FF",
        date="00.09.02*FF",
        address="60.01.01*FF",
        temperature="60.09.00*FF"
    )
