import serial


class Meter:
    """
    SDK for working with electricity meters Neva MT 3xx via serial port.
    """

    __init_baudrate = 300
    __working_baudrate = 9600
    password = b"00000000"
    serial_num = ""

    SOH = b"\x01"
    STX = b"\x02"
    ETX = b"\x03"
    ACK = b"\x06"
    NAK = b"\x15"
    DC3 = b"\x13"
    CRLF = b"\x0D\x0A"

    commands = {
        # /?!<CR><LF>
        "transfer_request": b"/?!%s" % CRLF,
        # <ACK>051<CR><LF>
        "init": b"%s051%s" % (ACK, CRLF),
        # <SOH>P1<STX>(<password>)<ETX>a
        "send_password": b"%sP1%s(<pass>)%sa" % (SOH, STX, ETX),
        # <SOH>R1<STX>0F0880FF()<ETX><NAK>
        "total_energy": b"%sR1%s0F0880FF()%s%s" % (SOH, STX, ETX, NAK),
        # <SOH>R1<STX>200700FF()<ETX>f
        "voltage_phase1": b"%sR1%s200700FF()%sf" % (SOH, STX, ETX),
        # <SOH>R1<STX>340700FF()<ETX>c
        "voltage_phase2": b"%sR1%s340700FF()%sc" % (SOH, STX, ETX),
        # <SOH>R1<STX>480700FF()<ETX>h
        "voltage_phase3": b"%sR1%s480700FF()%sh" % (SOH, STX, ETX),
        # <SOH>R1<STX>240700FF()<ETX>b
        "active_power_phase1": b"%sR1%s240700FF()%sb" % (SOH, STX, ETX),
        # <SOH>R1<STX>380700FF()<ETX>o
        "active_power_phase2": b"%sR1%s380700FF()%so" % (SOH, STX, ETX),
        # <SOH>R1<STX>4C0700FF()<ETX><DC3>
        "active_power_phase3": b"%sR1%s4C0700FF()%s%s" % (SOH, STX, ETX, DC3),
        # <SOH>R1<STX>100700FF()<ETX>e
        "active_power_phase_sum": b"%sR1%s100700FF()%se" % (SOH, STX, ETX),
        # <SOH>R1<STX>600100FF()<ETX>d
        "serial_num": b"%sR1%s600100FF()%sd" % (SOH, STX, ETX),
    }

    def __init__(self, port):
        self.port = port
        self.__start_session()

    def __start_session(self):
        """
        Starting serial session, sending initial commands.
        """

        self.session = serial.Serial(self.port,
                                     self.__init_baudrate,
                                     serial.SEVENBITS,
                                     serial.PARITY_EVEN,
                                     timeout=1)
        self.session.write(self.commands["transfer_request"])
        self.device_name = self.session.readall().replace(b"\r\n", b"") \
                                                 .replace(b"/TPC5", b"") \
                                                 .decode("utf-8")
        self.session.write(self.commands["init"])
        self.session.close()
        self.session.baudrate = self.__working_baudrate
        self.session.open()
        self.password = self.__parse_value(self.session.readall())
        self.session.write(self.commands["send_password"].replace(
            b"<pass>", self.password))
        self.session.readall()

    def get_total_energy(self) -> tuple[float]:
        """
        Returns accumulated active energy.
        """

        return self.__get_multi_val(self.commands["total_energy"])

    def get_phase_voltages(self) -> tuple[float]:
        """
        Returns current voltage of all phases.
        """

        v1 = float(self.__get_single_val(self.commands["voltage_phase1"]))
        v2 = float(self.__get_single_val(self.commands["voltage_phase2"]))
        v3 = float(self.__get_single_val(self.commands["voltage_phase3"]))
        return v1, v2, v3

    def get_active_power(self) -> tuple[float]:
        """
        Returns current active power (in watts) of all phases.
        """

        w_sum = float(
            self.__get_single_val(self.commands["active_power_phase_sum"]))
        w1 = float(self.__get_single_val(self.commands["active_power_phase1"]))
        w2 = float(self.__get_single_val(self.commands["active_power_phase2"]))
        w3 = float(self.__get_single_val(self.commands["active_power_phase3"]))
        return w_sum, w1, w2, w3

    def get_serial_number(self) -> int:
        if self.serial_num:
            return self.serial_num
        self.serial_num = self.__get_single_val(
            self.commands["serial_num"]).decode("ascii")
        return self.serial_num

    # TODO find command for this
    def is_screw_terminal_cover_removed(self) -> bool:
        pass

    def __get_single_val(self, command: bytes) -> bytes:
        self.session.write(command)
        return self.__parse_value(self.session.readall())

    def __get_multi_val(self, command: bytes) -> float:
        values = self.__get_single_val(command).split(b",")
        return tuple(map(float, values))

    def __parse_value(self, value: bytes) -> bytes:
        return value.split(b"(")[1].split(b")")[0]

    def __str__(self) -> str:
        return self.device_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()


if __name__ == "__main__":
    # TODO arg parsing
    pass
