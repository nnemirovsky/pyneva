from dataclasses import dataclass
from typing import NamedTuple, Union


class DataMsg(NamedTuple):
    data: Union[str, float, tuple[Union[str, float], ...]]
    address: str


class IdentificationMsg(NamedTuple):
    ident: str
    baudrate_num: int
    vendor: str


class CommandMsg(NamedTuple):
    data: bytes
    command: str
    address: str = ""


class Status(NamedTuple):
    data_memory_err: bool
    param_memory_err: bool
    measurement_err: bool
    clock_err: bool
    battery_discharged: bool
    programming_button_pressed: bool
    data_memory_doesnt_work: bool
    param_memory_doesnt_work: bool
    screw_terminal_cover_removed: bool
    load_connected: bool
    load_disconnected: bool


class TotalEnergy(NamedTuple):
    total: float
    T1: float
    T2: float
    T3: float
    T4: float


class Voltage(NamedTuple):
    phaseA: float
    phaseB: float
    phaseC: float


class ActivePower(NamedTuple):
    sum: float
    phaseA: float
    phaseB: float
    phaseC: float


class SeasonalSchedule(NamedTuple):
    month: int
    day: int
    weekday_skd_num: int
    sat_skd_num: int
    sun_skd_num: int


class SpecialDaysSchedule(NamedTuple):
    month: int
    day: int
    skd_num: int


class TariffSchedulePart(NamedTuple):
    hour: int
    minute: int
    T_num: int


class TariffSchedule(NamedTuple):
    parts: tuple[TariffSchedulePart, ...]


@dataclass(eq=False, frozen=True, unsafe_hash=True)
class OBISCodes:
    total_energy: str
    serial_num: str
    status: str
    seasonal_schedules: str
    special_days_schedules: str
    tariff_schedule_obis: str
    date: str
    address: str
    voltage: str = ""
    voltage_A: str = ""
    voltage_B: str = ""
    voltage_C: str = ""
    active_power: str = ""
    active_power_A: str = ""
    active_power_B: str = ""
    active_power_C: str = ""
    active_power_sum: str = ""
    temperature: str = ""


class MeterException(Exception):
    """Base class for meter exceptions."""


class MeterConnectionError(MeterException):
    """Raise if error occurs while connection initialization."""


class ResponseError(MeterException):
    """Base exception for incorrect responses."""


class WrongBCC(ResponseError):
    """Raise when the BCC is incorrect in a response message."""


class ErrorMessageReceived(MeterException):
    """Raise when an error message is received."""
