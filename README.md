## Library for electricity meters Neva MT

Working via serial port or RFC2217 server. 
IEC 61107 protocol is used (currently IEC 62056-21) and OBIS codes.

## Installation

```shell
python -m pip install pyneva
```

## Usage examples

### CLI

```shell
$ python -m pyneva connect -i rfc2217://192.168.88.109:1884 -m NevaMT324AOS --val active_energy current --obis 60.01.00*FF
Connected to: [NEVAMT324.1106 : 11111111]

Values:
total_energy     ActiveEnergy(total=16484.51, T1=12896.28, T2=3588.23, T3=0.0, T4=0.0)
active_power     ActivePower(phaseA=5.0, phaseB=1372.4, phaseC=122.3, total=1499.8)

OBIS:
60.01.00*FF      60089784
```

### Code

```python
from pyneva import NevaMT324AOS

# /dev/ttyX for linux local port
# comX or COMX for Windows local port
with NevaMT324AOS("rfc2217://192.168.88.109:1884") as meter:
    print(meter.model)
    # MT324 A OS 5(60)A

    print(meter.serial_number)
    # 11111111

    print(meter.active_energy)
    # ActiveEnergy(total=16348.84, T1=12790.08, T2=3558.76, T3=0.0, T4=0.0)

    print(meter.voltage)
    # Voltage(l1=233.81, l2=233.02, l3=232.15)

    print(meter.active_power)
    # ActivePower(l1=5.0, l2=1833.4, l3=130.3, total=1968.8)

    print(meter.seasonal_schedules)
    # (SeasonSchedule(month=1, day=1, weekday_skd_num=1, sat_skd_num=1, sun_skd_num=1),)
    # Returns tuple with seasonal schedules.
    # Each schedule specifies from which date the tariff starts,
    # and the numbers of tariff schedules on weekdays, Saturdays, Sundays separately.

    print(meter.special_days_schedules)
    # ()
    # Returns empty tuple if you have no special days tariff schedules (max 32 days).
    
    print(meter.tariff_schedules)
    # (
    #     TariffSchedule(parts=(
    #         TariffSchedulePart(hour=7, minute=0, T_num=1),
    #         TariffSchedulePart(hour=23, minute=0, T_num=2)
    #     )),
    # )
    # Returns tuple with tariff schedules.
    # Each tariff schedule contains parts of the schedule.
    # Each schedule part describes from what time of day the tariff starts
    # and tariff number (T1, T2, T3, T4).
```

## Supported models

- MT 324 A OS 5(60)A (NEVAMT324.11XX)
- MT 324 AR E4BS 5(60)A (NEVAMT324.25XX)
