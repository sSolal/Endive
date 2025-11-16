## The main app

from src.app import Cli
from tests import integration
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()
    if args.test:
        integration.run()
        exit(0)
    app = Cli(debug=args.debug)
    app.run()
