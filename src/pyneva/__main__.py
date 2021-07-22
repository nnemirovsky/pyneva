from pyneva.meter import Meter
import argparse

FUNCTIONS = ("total_energy", "voltage", "amperage", "serial_number", "status", "season_schedule",
             "tariff_schedules", "special_days_schedule")

parser = argparse.ArgumentParser(description="CLI version does not support write mode!\n")

parser.add_argument("--obis", nargs='*', default="", help="Specify OBIS codes")
parser.add_argument("--func", nargs='*', default="", choices=FUNCTIONS,
                    help="Specify prepared functions")
parser.add_argument("-p", "--port", required=True, help="Specify serial port interface")

args = parser.parse_args()

if len(args.obis) == 0 and len(args.func) == 0:
    parser.error("at least one of --obis and --func required")

try:
    with Meter(args.port) as session:
        print(f"Connected to: {session}")

        if len(args.obis) != 0:
            print("\nOBIS:")
            for code in args.obis:
                session.send_request(session.make_request(code))
                print(f"{code}\t", session.parse_response(session.get_response()))

        if len(args.func) != 0:
            print("\nFunctions:")
            for func in args.func:
                print(f"{func}\t", getattr(session, func))

except ConnectionError as e:
    parser.error(str(e))
