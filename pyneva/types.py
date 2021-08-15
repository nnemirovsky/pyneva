from dataclasses import dataclass
from typing import NamedTuple


class DataMsg(NamedTuple):
    data: tuple[str, ...]
    address: str


class IdentificationMsg(NamedTuple):
    identifier: str
    baudrate_num: int
    vendor: str


class ActiveEnergy(NamedTuple):
    total: float
    T1: float
    T2: float
    T3: float
    T4: float


class Voltage(NamedTuple):
    l1: float
    l2: float
    l3: float


class Current(NamedTuple):
    l1: float
    l2: float
    l3: float


class PowerFactor(NamedTuple):
    l1: str
    l2: str
    l3: str


class ActivePower(NamedTuple):
    l1: float
    l2: float
    l3: float
    total: float


class ReactivePower(NamedTuple):
    positive_l1: float
    negative_l1: float
    positive_l2: float
    negative_l2: float
    positive_l3: float
    negative_l3: float
    total_positive: float
    total_negative: float


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


@dataclass
class OBISCodes:
    serial_num: str
    firmware_id: str
    seasonal_schedules: str
    special_days_schedules: str
    tariff_schedule: str
    date: str
    time: str
    datetime: str
    address: str
    frequency: str
    active_energy: str = ""
    active_energy_prev_month: str = ""
    active_energy_prev_day: str = ""
    status: str = ""
    temperature: str = ""
    voltage_l1: str = ""
    voltage_l2: str = ""
    voltage_l3: str = ""
    current_l1: str = ""
    current_l2: str = ""
    current_l3: str = ""
    power_factor_l1: str = ""
    power_factor_l2: str = ""
    power_factor_l3: str = ""
    active_power_l1: str = ""
    active_power_l2: str = ""
    active_power_l3: str = ""
    active_power_sum: str = ""
    positive_reactive_power_l1: str = ""
    negative_reactive_power_l1: str = ""
    positive_reactive_power_l2: str = ""
    negative_reactive_power_l2: str = ""
    positive_reactive_power_l3: str = ""
    negative_reactive_power_l3: str = ""
    positive_reactive_power_sum: str = ""
    negative_reactive_power_sum: str = ""


class MeterException(Exception):
    """Base class for meter exceptions."""


class MeterConnectionError(MeterException):
    """Raise if error occurs while connection initialization."""


class ResponseError(MeterException):
    """Base exception for incorrect/error responses."""


class WrongBCC(ResponseError):
    """Raise when the BCC is incorrect in a response message."""

# class ErrorMessageReceived(MeterException):
#     """Raise when an error message is received."""
