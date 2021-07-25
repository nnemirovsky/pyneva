from .core import Meter
import argparse
from . import tools


def is_property(attr: str) -> bool:
    return type(getattr(Meter, attr)) == property


FUNCTIONS = frozenset(filter(is_property, dir(Meter)))

parser = argparse.ArgumentParser(description="CLI version does not support write mode!\n")

parser.add_argument("--obis", nargs='*', default="", help="Specify OBIS code(-s)")
parser.add_argument("--func", nargs='*', default="", choices=FUNCTIONS,
                    help="Specify prepared function(-s)")
parser.add_argument("-p", "--port", required=True, help="Specify serial port interface")

args = parser.parse_args()

if len(args.obis) == 0 and len(args.func) == 0:
    parser.error("at least one of --obis and --func required")

try:
    with Meter(args.port) as meter:
        print(f"Connected to: {meter}")

        if len(args.obis) != 0:
            print("\nOBIS:")
            for code in args.obis:
                meter.send_request(tools.make_request(code))
                print(f"{code}\t", tools.parse_response(meter.get_response()))

        if len(args.func) != 0:
            print("\nFunctions:")
            for func in args.func:
                print(f"{func}\t", getattr(meter, func))

except ConnectionError as e:
    parser.error(str(e))
