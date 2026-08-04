from argparse import ArgumentParser
from pathlib import Path

from scheduler import count_task_preemptions, dm_schedule
from workload import load_workload


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

    workload = load_workload(args.workload)
    hyperperiod_schedule = dm_schedule(workload)

    if hyperperiod_schedule is None:
        # unschedulable
        print("0")
    else:
        # count the number of pre-emptions associated with a task
        preempt_counts = count_task_preemptions(workload, hyperperiod_schedule)
        counts = [str(preempt_counts[task]) for task in workload.tasks]

        print("1")
        print(",".join(counts))


if __name__ == "__main__":
    main()
