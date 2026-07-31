from argparse import ArgumentParser
from pathlib import Path


def main():
    parser = ArgumentParser(
        "ece652_final",
        "implements deadline monotonic scheduling algorithm accoridng to assignment instructions",
    )
    parser.add_argument(
        "workload",
        help="path to workload specification",
        type=Path,
    )
    args = parser.parse_args()

    print(args.workload)


if __name__ == "__main__":
    main()
