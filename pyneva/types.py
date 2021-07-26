from typing import NamedTuple


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
