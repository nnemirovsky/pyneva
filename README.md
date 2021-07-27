## Library for electricity meters Neva MT 3xx

Working via serial port using protocol IEC 61107 (currently IEC 62056-21) and OBIS codes

## Installation

### From PyPI

```shell
python -m pip install pyneva
```

### Development environment

```shell
git clone https://github.com/vazelegend/pyneva
cd pyneva
python -m venv .venv
````

```shell
source ./.venv/bin/activate #Linux
or
.\.venv\Scripts\activate #Windows
```

```shell
python -m pip install -r requirements.txt
```

## Usage

```python
from pyneva import Meter

# /dev/ttyX for linux
with Meter("COM4") as session:
    print(session.device_name)
    # NEVAMT324.1106
    
    print(session.serial_number)
    # 11111111
    
    print(session.total_energy)
    # TotalEnergy(total=16348.84, T1=12790.08, T2=3558.76, T3=0.0, T4=0.0)
    
    print(session.voltage)
    # Voltage(phaseA=233.81, phaseB=233.02, phaseC=232.15)
    
    print(session.active_power)
    # ActivePower(sum=1968.8, phaseA=5.0, phaseB=1833.4, phaseC=130.3)
    
    print(session.seasonal_schedules)
    # (SeasonSchedule(month=1, day=1, weekday_skd_num=1, sat_skd_num=1, sun_skd_num=1),)
    # Returns tuple with seasonal schedules (SeasonSchedule objects).
    # Each schedule specifies from which date the tariff starts,
    # and the numbers of tariff schedules on weekdays, Saturdays, Sundays separately.
    
    print(session.special_days_schedules)
    # ()
    # Returns empty tuple if you have no special days tariff schedules (max 32 days)
    
    print(session.tariff_schedules)
    # (TariffSchedule(parts=(TariffSchedulePart(hour=7, minute=0, T_num=1), TariffSchedulePart(hour=23, minute=0, T_num=2))),)
    # Returns tuple with tariff schedules (TariffSchedule objects).
    # Each tariff schedule contains parts of the schedule (TariffSchedulePart objects).
    # Each schedule part describes from what time of day the tariff starts and tariff number (T1, T2, T3, T4).
```
