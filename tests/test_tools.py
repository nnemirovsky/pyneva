import unittest

from pyneva.tools import make_cmd_msg, parse_data_msg, parse_id_msg, parse_password_msg, \
    parse_schedules, calculate_bcc
from pyneva.types import SeasonalSchedule, IdentificationMsg, ResponseError, WrongBCC


class TestTools(unittest.TestCase):
    def test_make_cmd_msg(self):
        first = (
            make_cmd_msg("60.01.00*FF"),
            make_cmd_msg(mode="P", data=b"00000000"),
        )
        second = (
            b"\x01R1\x02600100FF()\x03d",
            b"\x01P1\x02(00000000)\x03a",
        )
        self.assertEqual(first, second)

        self.assertRaises(TypeError, make_cmd_msg, obis=b"60.01.00*FF")
        self.assertRaises(TypeError, make_cmd_msg, obis=435)
        self.assertRaises(TypeError, make_cmd_msg, mode="W", data=12231)
        self.assertRaises(ValueError, make_cmd_msg, obis="60.01.00*FF", mode="L")
        self.assertRaises(ValueError, make_cmd_msg, mode="W")
        self.assertRaises(ValueError, make_cmd_msg, mode="P")
        self.assertRaises(ValueError, make_cmd_msg, mode="W")
        self.assertRaises(ValueError, make_cmd_msg, obis="", mode="W")
        self.assertRaises(ValueError, make_cmd_msg, obis="60.01.00*FF", mode="P")
        self.assertRaises(ValueError, make_cmd_msg, obis="600100FF")

    def test_parse_data_msg(self):
        first = (
            parse_data_msg(b"\x02600100FF(60089784)\x03\x09").data,
            parse_data_msg(b"\x024C0700FF(00134.2)\x03X").data,
            parse_data_msg(b"\x020F0680FF(04.8190,04.8457,02.5359,00.0000,00.0000)\x03R").data,
            parse_data_msg(
                b"\x020A0164FF(070001,230002,000000,000000,000000,000000,000000,000000)\x03Y"
            ).data,
        )
        second = (
            ("60089784",),
            ("00134.2",),
            ("04.8190", "04.8457", "02.5359", "00.0000", "00.0000"),
            ("070001", "230002", "000000", "000000", "000000", "000000", "000000", "000000"),
        )
        self.assertEqual(first, second)

        self.assertRaises(TypeError, parse_data_msg, response=123)
        self.assertRaises(ResponseError, parse_data_msg, response=b"")
        self.assertRaises(ResponseError, parse_data_msg, response=b"\x024C0700FF00134.2\x03X")
        # Invalid BCC
        self.assertRaises(WrongBCC, parse_data_msg, response=b"\x020F0880FF(016442.17,012865.25,00"
                                                             b"3576.92,000000.00,000000.00)\x03S")

    def test_parse_id_msg(self):
        first = (
            parse_id_msg(b"/TPC5NEVAMT324.1106\r\n"),
            parse_id_msg(b"/CPz3NEVAMT123.2302\r\n"),
            parse_id_msg(b"/SAT5EM72000656621\r\n"),
        )
        second = (
            IdentificationMsg(identifier="NEVAMT324.1106", vendor="TPC", baudrate_num=5),
            IdentificationMsg(identifier="NEVAMT123.2302", vendor="CPz", baudrate_num=3),
            IdentificationMsg(identifier="EM72000656621", vendor="SAT", baudrate_num=5),
        )
        self.assertEqual(first, second)

        self.assertRaises(TypeError, parse_id_msg, response=123)
        self.assertRaises(TypeError, parse_id_msg, response="abc")
        self.assertRaises(ResponseError, parse_id_msg, response=b"")
        self.assertRaises(ResponseError, parse_id_msg, response=b"/TPC6NEVAMT324.1106\r\n")
        self.assertRaises(ResponseError, parse_id_msg, response=b"/TpC6NEVAMT324.1106\r\n")
        self.assertRaises(ResponseError, parse_id_msg, response=b"/SAT5EM72000656621abcd\r\n")
        self.assertRaises(ResponseError, parse_id_msg, response=b"/SAT5EM720006566211234\r\n")

    def test_parse_password_msg(self):
        first = (
            parse_password_msg(b"\x01P0\x02(00000000)\x03`"),
            parse_password_msg(b"\x01P0\x02(9)\x03Y"),
            parse_password_msg(b"\x01P0\x02()\x03`"),
        )
        second = (
            b"00000000",
            b"9",
            b"",
        )
        self.assertEqual(first, second)

        self.assertRaises(TypeError, parse_password_msg, response=123)
        self.assertRaises(TypeError, parse_password_msg, response="abc")
        self.assertRaises(ResponseError, parse_password_msg, response=b"")
        self.assertRaises(ResponseError, parse_password_msg, response=b"P0\x02(00000000)\x03`")
        self.assertRaises(ResponseError, parse_password_msg, response=b"\x01P3\x02(00000000)\x03`")
        self.assertRaises(ResponseError, parse_password_msg, response=b"\x01P0\x02\x03`")
        # Invalid BCC
        self.assertRaises(WrongBCC, parse_password_msg, response=b"\x01P0\x02(00000000)\x03s")

    def test_parse_schedules(self):
        first = (
            parse_schedules(("0731010102", "0000000000", "0000000000", "0000000000", "0000000000",
                             "0000000000", "0000000000", "0000000000", "0000000000", "0000000000",
                             "0000000000", "0000000000")),

            parse_schedules(("0731010102", "0801020102", "0000000000", "0000000000", "0000000000",
                             "0000000000", "0000000000", "0000000000", "0000000000", "0000000000",
                             "0000000000", "0000000000")),

            parse_schedules(("0731010102", "0000000000", "1206021104", "0000000000", "0000000000",
                             "0000000000", "0000000000", "0000000000", "0000000000", "0000000000",
                             "0000000000", "0000000000")),
        )
        second = (
            (SeasonalSchedule(month=7, day=31, weekday_skd_num=1, sat_skd_num=1, sun_skd_num=2),),

            (SeasonalSchedule(month=7, day=31, weekday_skd_num=1, sat_skd_num=1, sun_skd_num=2),
             SeasonalSchedule(month=8, day=1, weekday_skd_num=2, sat_skd_num=1, sun_skd_num=2),),

            (SeasonalSchedule(month=7, day=31, weekday_skd_num=1, sat_skd_num=1, sun_skd_num=2),
             SeasonalSchedule(month=12, day=6, weekday_skd_num=2, sat_skd_num=11, sun_skd_num=4),),
        )
        self.assertEqual(first, second)

    def test_calculate_bcc(self):
        first = (
            calculate_bcc(b"60010AFF(0000000000000000)\x03"),
            calculate_bcc(b"R1\x0260010AFF()\x03"),
        )
        second = (b"t", b"\x15",)
        self.assertEqual(first, second)

        self.assertRaises(TypeError, calculate_bcc, data=123)


if __name__ == '__main__':
    unittest.main()
