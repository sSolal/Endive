## The main app

from src.app import Cli
from tests import integration
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("file", nargs="?", help="Path to .end file to execute")

    args = parser.parse_args()
    if args.test:
        integration.run(silent=not args.debug)
        exit(0)

    app = Cli(debug=args.debug)

    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                if line.strip() == "":
                    continue
                print(line.strip())
                app.process(line.strip())
    else:
        app.run()
