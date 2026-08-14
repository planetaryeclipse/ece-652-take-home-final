from dataclasses import dataclass
from pathlib import Path

from constants import TIME_PRECISION


@dataclass
class Task:
    exec_time: float
    period: float
    rel_deadline: float


@dataclass
class Workload:
    tasks: list[Task]

    def set_factor(self, factor: float):
        # utility only for testing
        for task in self.tasks:
            task.exec_time = round(factor * float(task.exec_time), TIME_PRECISION)
            task.period = round(factor * float(task.period), TIME_PRECISION)
            task.rel_deadline = round(factor * float(task.rel_deadline), TIME_PRECISION)


# workload methods


def parse_workload_file(workload: str) -> Workload:
    """loads a workload from the string specification"""
    tasks = []
    for task_desc in workload.split():
        if task_desc.isspace():
            continue
        tasks.append(Task(*[float(val) for val in task_desc.split(",")]))
    return Workload(tasks)


def load_workload(path: Path) -> Workload:
    """loads a workload from specification at provided path"""
    with open(path, "r") as file:
        return parse_workload_file(file.read())
