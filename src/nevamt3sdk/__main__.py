from nevamt3sdk.meter import Meter
import argparse

FUNCTION_MAP = ("get_total_energy", "get_phase_voltages", "get_active_power",
                "get_serial_number")

parser = argparse.ArgumentParser()

parser.add_argument("commands", choices=FUNCTION_MAP, nargs="+")
parser.add_argument("-p",
                    "--port",
                    dest="port",
                    required=True,
                    help="Specify serial port interface")

args = parser.parse_args()

with Meter(args.port) as session:
    for cmd in args.commands:
        print(getattr(session, cmd)())
