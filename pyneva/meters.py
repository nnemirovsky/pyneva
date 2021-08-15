from .types import Current, Voltage, PowerFactor, ActivePower, ReactivePower
from . import tools
from .core import MeterBase


class NevaMT3(MeterBase):
    """Base class for three-phase meters (Neva MT 3xx)."""

    # def __init__(self, interface: str, address: str = "", password: str = "",
    #              initial_baudrate: int = 0):
    #     super().__init__(interface, address, password, initial_baudrate)
    #     self.obis_codes.voltage_l1 = "20.07.00*FF"
    #     self.obis_codes.voltage_l2 = "34.07.00*FF"
    #     self.obis_codes.voltage_l3 = "48.07.00*FF"
    #     self.obis_codes.active_power_l1 = "24.07.00*FF"
    #     self.obis_codes.active_power_l2 = "38.07.00*FF"
    #     self.obis_codes.active_power_l3 = "4C.07.00*FF"
    #     self.obis_codes.active_power_sum = "10.07.00*FF"
    #     self.obis_codes.current_l1 = "1F.07.00*FF"
    #     self.obis_codes.current_l2 = "33.07.00*FF"
    #     self.obis_codes.current_l3 = "47.07.00*FF"
    #     self.obis_codes.power_factor_l1 = "21.07.FF*FF"
    #     self.obis_codes.power_factor_l2 = "35.07.FF*FF"
    #     self.obis_codes.power_factor_l3 = "49.07.FF*FF"

    @property
    def voltage_l1(self) -> float:
        """Instantaneous voltage in phase L1 [V]."""
        self.send(tools.make_cmd_msg(self.obis_codes.voltage_l1))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def voltage_l2(self) -> float:
        """Instantaneous voltage in phase L2 [V]."""
        self.send(tools.make_cmd_msg(self.obis_codes.voltage_l2))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def voltage_l3(self) -> float:
        """Instantaneous voltage in phase L3 [V]."""
        self.send(tools.make_cmd_msg(self.obis_codes.voltage_l3))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def voltage(self) -> Voltage:
        """Instantaneous voltages of all phases [V]."""
        return Voltage(self.voltage_l1, self.voltage_l2, self.voltage_l3)

    @property
    def current_l1(self) -> float:
        """Instantaneous current in phase L1 [A]."""
        self.send(tools.make_cmd_msg(self.obis_codes.current_l1))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def current_l2(self) -> float:
        """Instantaneous current in phase L2 [A]."""
        self.send(tools.make_cmd_msg(self.obis_codes.current_l2))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def current_l3(self) -> float:
        """Instantaneous current in phase L3 [A]."""
        self.send(tools.make_cmd_msg(self.obis_codes.current_l3))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def current(self) -> Current:
        """Instantaneous currents of all phases [A]."""
        return Current(self.current_l1, self.current_l2, self.current_l3)

    def __get_power_factor(self, obis: str) -> str:
        y = ("C", "L", "?")
        self.send(tools.make_cmd_msg(obis))
        resp = tools.parse_data_msg(self.recv(19)).data[0]
        return y[int(resp[0])] + str(float(resp[1:]))

    @property
    def power_factor_l1(self) -> str:
        """Power factor in phase L1."""
        return self.__get_power_factor(self.obis_codes.power_factor_l1)

    @property
    def power_factor_l2(self) -> str:
        """Power factor in phase L2."""
        return self.__get_power_factor(self.obis_codes.power_factor_l3)

    @property
    def power_factor_l3(self) -> str:
        """Power factor in phase L3."""
        return self.__get_power_factor(self.obis_codes.power_factor_l3)

    @property
    def power_factor(self) -> PowerFactor:
        """Power factors of all phases."""
        return PowerFactor(self.power_factor_l1, self.power_factor_l2, self.power_factor_l3)

    @property
    def active_power_l1(self) -> float:
        """Active instantaneous power in phase L1 [W]."""
        self.send(tools.make_cmd_msg(self.obis_codes.active_power_l1))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def active_power_l2(self) -> float:
        """Active instantaneous power in phase L2 [W]."""
        self.send(tools.make_cmd_msg(self.obis_codes.active_power_l1))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def active_power_l3(self) -> float:
        """Active instantaneous power in phase L3 [W]."""
        self.send(tools.make_cmd_msg(self.obis_codes.active_power_l2))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def active_power_sum(self) -> float:
        """Sum of active instantaneous power of all phases [W]."""
        self.send(tools.make_cmd_msg(self.obis_codes.active_power_sum))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def active_power(self) -> ActivePower:
        """Active instantaneous power of all phases and total [W]."""
        return ActivePower(l1=self.active_power_l1, l2=self.active_power_l2,
                           l3=self.active_power_l3, total=self.active_power_sum)


class NevaMT3R(NevaMT3):
    """Class for meters Neva MT3XX supporting reactive energy."""
    #
    # def __init__(self, interface: str, address: str = "", password: str = "",
    #              initial_baudrate: int = 0):
    #     super().__init__(interface, address, password, initial_baudrate)
    #     self.obis_codes.positive_reactive_power_l1 = "17.07.01*FF"
    #     self.obis_codes.negative_reactive_power_l1 = "18.07.01*FF"
    #     self.obis_codes.positive_reactive_power_l2 = "2B.07.01*FF"
    #     self.obis_codes.negative_reactive_power_l2 = "2C.07.01*FF"
    #     self.obis_codes.positive_reactive_power_l3 = "3F.07.01*FF"
    #     self.obis_codes.negative_reactive_power_l3 = "40.07.01*FF"
    #     self.obis_codes.positive_reactive_power_sum = "03.07.01*FF"
    #     self.obis_codes.negative_reactive_power_sum = "04.07.01*FF"

    @property
    def positive_reactive_power_l1(self) -> float:
        """Positive reactive power of phase L1."""
        self.send(tools.make_cmd_msg(self.obis_codes.positive_reactive_power_l1))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def negative_reactive_power_l1(self) -> float:
        """Negative reactive power of phase L1."""
        self.send(tools.make_cmd_msg(self.obis_codes.negative_reactive_power_l1))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def positive_reactive_power_l2(self) -> float:
        """Positive reactive power of phase L2."""
        self.send(tools.make_cmd_msg(self.obis_codes.positive_reactive_power_l2))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def negative_reactive_power_l2(self) -> float:
        """Negative reactive power of phase L2."""
        self.send(tools.make_cmd_msg(self.obis_codes.negative_reactive_power_l2))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def positive_reactive_power_l3(self) -> float:
        """Positive reactive power of phase L3."""
        self.send(tools.make_cmd_msg(self.obis_codes.positive_reactive_power_l3))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def negative_reactive_power_l3(self) -> float:
        """Negative reactive power of phase L3."""
        self.send(tools.make_cmd_msg(self.obis_codes.negative_reactive_power_l3))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def positive_reactive_power_sum(self) -> float:
        """Sum of all positive reactive powers."""
        self.send(tools.make_cmd_msg(self.obis_codes.positive_reactive_power_sum))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def negative_reactive_power_sum(self) -> float:
        """Sum of all negative reactive powers."""
        self.send(tools.make_cmd_msg(self.obis_codes.negative_reactive_power_sum))
        return float(tools.parse_data_msg(self.recv(20)).data[0])

    @property
    def reactive_power(self) -> ReactivePower:
        """All reactive powers (positive and negative)."""
        return ReactivePower(self.positive_reactive_power_l1, self.negative_reactive_power_l1,
                             self.positive_reactive_power_l2, self.negative_reactive_power_l2,
                             self.positive_reactive_power_l3, self.negative_reactive_power_l3,
                             self.positive_reactive_power_sum, self.negative_reactive_power_sum)


class NevaMT324AOS(NevaMT3):
    """Class for meters Neva MT324AOS."""

    @property
    def status(self) -> dict[str, bool]:
        """Current status of the meter."""
        self.send(tools.make_cmd_msg(self.obis_codes.status))
        response = tools.parse_data_msg(self.recv(17)).data[0]
        status = ("bodyIsOpen", "terminalCoverIsRemoved", "loadIsConnected", "loadIsDisconnected",
                  "failedToChangeRelayStatus", "influenceOfMagneticField", "wrongWired",
                  "dataMemoryICWorkError", "paramMemoryWorkError", "powerICError",
                  "clockOrCalendarFailure", "batteryDischarge",
                  "triggerOfButtonOfProgrammingPermission", "dataMemoryFailure",
                  "paramMemoryFailure")
        bits = f'{int(response, 16):0>16b}'
        return dict((status[idx], bit == "1") for idx, bit in enumerate(bits[:7] + bits[8:]))

    @property
    def power_factor_l1(self) -> float:
        """Power factor in phase L1."""
        self.send(tools.make_cmd_msg(self.obis_codes.power_factor_l1))
        return float(tools.parse_data_msg(self.recv(18)).data[0])

    @property
    def power_factor_l2(self) -> float:
        """Power factor in phase L2."""
        self.send(tools.make_cmd_msg(self.obis_codes.power_factor_l2))
        return float(tools.parse_data_msg(self.recv(18)).data[0])

    @property
    def power_factor_l3(self) -> float:
        """Power factor in phase L3."""
        self.send(tools.make_cmd_msg(self.obis_codes.power_factor_l3))
        return float(tools.parse_data_msg(self.recv(18)).data[0])


class NevaMT324R(NevaMT3R):
    """Class for working with electricity meters Neva MT 324
    supporting reactive energy.
    """
