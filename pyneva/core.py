from collections import namedtuple
from datetime import datetime
from time import sleep

import serial
from serial.rfc2217 import Serial as rfc2217Serial

from . import tools
from .types import OBISCodes, ResponseError, MeterConnectionError, SeasonalSchedule, \
    SpecialDaysSchedule, TariffSchedule, TariffSchedulePart, ActiveEnergy


class MeterBase:
    """Base class for working with electricity meters Neva MT.
    Implements basic methods, excluding those that depend on the meter type.
    """

    __baudrates = (300, 600, 1200, 2400, 4800, 9600)
    __timeout = 3
    __serial_num = None
    __device_identifier = None
    __used_tariff_schedules = set()
    obis_codes = OBISCodes(serial_num="60.01.00*FF", date="00.09.02*FF", time="00.09.01*FF",
                           address="60.01.01*FF", status="60.05.00*FF", temperature="60.09.00*FF",
                           seasonal_schedules="0D.00.00*FF", special_days_schedules="0B.00.00*FF",
                           tariff_schedule="0A.%s.64*FF", firmware_id="60.01.04*FF",
                           frequency="0E.07.01*FF", datetime="00.09.80*FF",
                           active_energy="0F.08.80*FF", active_energy_prev_month="0F.08.80*00",
                           active_energy_prev_day="0F.80.80*00", voltage_l1="20.07.00*FF",
                           voltage_l2="34.07.00*FF", voltage_l3="48.07.00*FF",
                           active_power_l1="24.07.00*FF", active_power_l2="38.07.00*FF",
                           active_power_l3="4C.07.00*FF", active_power_sum="10.07.00*FF",
                           current_l1="1F.07.00*FF", current_l2="33.07.00*FF",
                           current_l3="47.07.00*FF", power_factor_l1="21.07.FF*FF",
                           power_factor_l2="35.07.FF*FF", power_factor_l3="49.07.FF*FF",
                           positive_reactive_power_l1="17.07.01*FF",
                           negative_reactive_power_l1="18.07.01*FF",
                           positive_reactive_power_l2="2B.07.01*FF",
                           negative_reactive_power_l2="2C.07.01*FF",
                           positive_reactive_power_l3="3F.07.01*FF",
                           negative_reactive_power_l3="40.07.01*FF",
                           positive_reactive_power_sum="03.07.01*FF",
                           negative_reactive_power_sum="04.07.01*FF")

    def __init__(self, interface: str, address: str = "", password: str = "",
                 initial_baudrate: int = 0):
        if initial_baudrate == 0:
            initial_baudrate = self.__baudrates[0]
        self.__interface = interface
        self.__address = address
        self.__password = password.encode("ascii")
        self.__init_baudrate = initial_baudrate
        self.__session = serial.serial_for_url(self.__interface, do_not_open=True,
                                               baudrate=self.__init_baudrate,
                                               bytesize=serial.SEVENBITS,
                                               parity=serial.PARITY_EVEN,
                                               stopbits=serial.STOPBITS_ONE,
                                               timeout=self.__timeout)
        self.__is_rfc2217 = isinstance(self.__session, rfc2217Serial)

    def start_session(self):
        """Starting serial session according to protocol IEC 61107 in programming mode."""
        self.__session.open()

        # Send request message
        self.send(b"/?%s!\r\n" % self.__address.encode("ascii"))

        working_baudrate_num = self.__read_id_msg()

        # Send acknowledgement message, programming mode
        self.send(b"\x060%i1\r\n" % working_baudrate_num)

        # Change baudrate
        sleep(.3)
        self.__session.baudrate = self.__baudrates[working_baudrate_num]

        self.__read_password_msg()

        # Send password comparison message
        self.send(tools.make_cmd_msg(mode="P", data=self.__password))

        self.__read_ack_msg()

    @property
    def seasonal_schedules(self) -> tuple[SeasonalSchedule, ...]:
        """Return tuple with seasonal schedules.
        Each schedule specifies from which date the tariff starts,
        and the numbers of tariff schedules on weekdays, Saturdays, Sundays separately.
        """
        self.send(tools.make_cmd_msg(self.obis_codes.seasonal_schedules))
        schedules = tools.parse_data_msg(self.recv(144)).data
        schedules = tools.parse_schedules(schedules)
        schedules = tuple(
            self.__parse_into_used_schedules(SeasonalSchedule, skd, (2, 3, 4)) for skd in schedules
        )
        return schedules

    @property
    def special_days_schedules(self) -> tuple[SpecialDaysSchedule, ...]:
        """Return tuple with special days schedules.
        Each schedule includes date and tariff schedule number.
        """
        self.send(tools.make_cmd_msg(self.obis_codes.special_days_schedules))
        days = tools.parse_data_msg(self.recv(236)).data
        days = tools.parse_schedules(days)
        days = tuple(
            self.__parse_into_used_schedules(SpecialDaysSchedule, skd, (3,)) for skd in days
        )
        return days

    def __parse_into_used_schedules(self, struct: namedtuple, skd: tuple[int, ...],
                                    nums: tuple[int, ...]) -> namedtuple:
        self.__used_tariff_schedules.update(map(lambda i: skd[i], nums))
        return struct(*skd)

    @property
    def tariff_schedules(self) -> tuple[TariffSchedule, ...]:
        """Return tuple with tariff schedules.
        Each tariff schedule contains parts of the schedule.
        Each schedule part describes from what time of day the tariff starts,
        and tariff number.
        """
        if not self.__used_tariff_schedules:
            self.__used_tariff_schedules.add(1)
        tariff_schedules = []
        for schedule_num in self.__used_tariff_schedules:
            schedule_obis = self.obis_codes.tariff_schedule % f"{schedule_num:02X}"
            self.send(tools.make_cmd_msg(schedule_obis))
            schedule = tools.parse_schedules(tools.parse_data_msg(self.recv(68)).data)
            schedule = tuple(TariffSchedulePart(*skd_part) for skd_part in schedule)
            if schedule:
                tariff_schedules.append(TariffSchedule(schedule))
        return tuple(tariff_schedules)

    @property
    def active_energy(self) -> ActiveEnergy:
        """Cumulative active energy from the first start of measurement
        to the present (Total, T1, ..., T4) [kWh].
        """
        self.send(tools.make_cmd_msg(self.obis_codes.active_energy))
        return ActiveEnergy(*map(float, tools.parse_data_msg(self.recv(62)).data))

    @property
    def active_energy_last_month(self) -> ActiveEnergy:
        """Cumulative active energy for this month (Total, T1, ..., T4) [kWh]."""
        zipped_values = zip(self.active_energy, self.__active_energy_prev_month)
        calc_values = map(lambda x: round(x[0] - x[1], 2), zipped_values)
        return ActiveEnergy(*calc_values)

    @property
    def active_energy_last_day(self) -> ActiveEnergy:
        """Cumulative active energy for this day (Total, T1, ..., T4) [kWh]."""
        zipped_values = zip(self.active_energy, self.__active_energy_prev_day)
        calc_values = map(lambda x: round(x[0] - x[1], 2), zipped_values)
        return ActiveEnergy(*calc_values)

    @property
    def __active_energy_prev_month(self) -> ActiveEnergy:
        """Cumulative active energy from the first start of measurement
        to the beginning of this month (Total, T1, ..., T4) [kWh].
        """
        self.send(tools.make_cmd_msg(self.obis_codes.active_energy_prev_month))
        return ActiveEnergy(*map(float, tools.parse_data_msg(self.recv(62)).data))

    @property
    def __active_energy_prev_day(self) -> ActiveEnergy:
        """Cumulative active energy from the first start of measurement
        to the beginning of this day (Total, T1, ..., T4) [kWh].
        """
        self.send(tools.make_cmd_msg(self.obis_codes.active_energy_prev_day))
        return ActiveEnergy(*map(float, tools.parse_data_msg(self.recv(62)).data))

    @property
    def frequency(self) -> float:
        """Supply frequency [Hz]."""
        self.send(tools.make_cmd_msg(self.obis_codes.frequency))
        return float(tools.parse_data_msg(self.recv(18)).data[0])

    @property
    def date(self) -> datetime.date:
        """Current date on the meter."""
        self.send(tools.make_cmd_msg(self.obis_codes.date))
        date_str = tools.parse_data_msg(self.recv(19)).data[0]
        return datetime.strptime(date_str, "%y%m%d").date()

    @property
    def time(self) -> datetime.time:
        """Current time on the meter."""
        self.send(tools.make_cmd_msg(self.obis_codes.time))
        time_str = tools.parse_data_msg(self.recv(19)).data[0]
        return datetime.strptime(time_str, "%H%M%S").time()

    @property
    def datetime(self) -> datetime:
        """Current date and time on the meter."""
        self.send(tools.make_cmd_msg(self.obis_codes.datetime))
        datetime_str = tools.parse_data_msg(self.recv(25)).data[0]
        return datetime.strptime(datetime_str, "%y%m%d%H%M%S")

    @property
    def serial_number(self) -> str:
        """Serial number of the meter."""
        if not self.__serial_num:
            self.send(tools.make_cmd_msg(self.obis_codes.serial_num))
            self.__serial_num = tools.parse_data_msg(self.recv(21)).data[0]
        return self.__serial_num

    @property
    def identifier(self) -> str:
        """Meter identifier obtained at initialization."""
        return self.__device_identifier

    @property
    def model(self) -> str:
        """Meter model obtained from the identifier."""
        return tools.id_to_model.get(self.identifier[6:12], "unknown identifier")

    @property
    def version(self) -> str:
        """Meter version of model."""
        return self.identifier[12:]

    @property
    def address(self) -> str:
        """Address of the meter (may be the same as the serial number)."""
        if self.__address:
            return self.__address
        self.send(tools.make_cmd_msg(self.obis_codes.address))
        self.__address = tools.parse_data_msg(self.recv(21)).data[0]
        return self.__address

    @property
    def firmware(self) -> str:
        """Meter firmware identifier."""
        self.send(tools.make_cmd_msg(self.obis_codes.firmware_id))
        return tools.parse_data_msg(self.recv(21)).data[0]

    @property
    def temperature(self) -> int:
        """Meter temperature [°С]."""
        self.send(tools.make_cmd_msg(self.obis_codes.temperature))
        temp_str = tools.parse_data_msg(self.recv(16)).data[0]
        if temp_str[0] == "1":
            temp_str = f"-{temp_str[1:]}"
        return int(temp_str)

    def __read_id_msg(self) -> int:
        try:
            msg = tools.parse_id_msg(self.recv(21))
            self.__device_identifier = msg.identifier
        except ResponseError as e:
            self.__session.__del__()
            raise MeterConnectionError(e) from None
        return msg.baudrate_num

    def __read_password_msg(self):
        try:
            # In my case the first (SOH) character is usually not received
            if self.__is_rfc2217:
                pass_msg = self.recv(15)
                # If not received first (SOH) char
                if pass_msg[0] != 1:
                    pass_msg = b"\x01" + pass_msg
                # If not received last (BCC) char
                if pass_msg[-1] == 3:
                    pass_msg += self.recv(1)
            else:
                pass_msg = self.recv(16)

            if not self.__password:
                self.__password = tools.parse_password_msg(pass_msg)
        except (ResponseError, IndexError) as e:
            self.__session.__del__()
            raise MeterConnectionError(e) from None

    def __read_ack_msg(self):
        try:
            msg = self.recv(1)
            if msg != b"\x06":
                msg += self.recv()
            tools.check_err(msg)
        except ResponseError as e:
            self.__session.__del__()
            raise MeterConnectionError(f"expected ACK message, but {e}") from None
        else:
            if msg != b"\x06":
                self.__session.__del__()
                raise MeterConnectionError(f"expected ACK message, but received {msg}") from None

    def send(self, message: bytes):
        """Send sequence of bytes to meter."""
        self.__session.write(message)

    def recv(self, size: int = None, expected: bytes = b"\x03") -> bytes:
        """Read sequence of bytes from the meter.

        If expected == None and size == None and session by RFC2217 protocol,
        the RawIOBase.readall method is called (read all bytes before timeout).

        Args:
            size: size of bytes, None by default.
                If specified, the Serial.read method is called (read
                 size bytes).
            expected: expected sequence, ETX char by default.
                If specified, SerialBase.read_until method is called (reads
                until an expected sequence is found).

        Returns:
            sequence of bytes

        Raises:
            ResponseError: if `expected` is ETX character, but the last
             2 chars are not received.
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

    def close_session(self):
        self.send(b"\x01B0\x03q")
        self.__session.flush()

    def __del__(self):
        self.__session.__del__()

    def __str__(self) -> str:
        return f"[{self.identifier} : {self.address}]"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__interface!r}, {self.address!r}, " \
               f"{self.__password.decode('ascii')!r}, {self.__init_baudrate})"

    def __enter__(self):
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_session()
        self.__del__()
