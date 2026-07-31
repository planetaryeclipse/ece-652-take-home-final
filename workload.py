from dataclasses import dataclass
from pathlib import Path


@dataclass
class Task:
    exec_time: float
    period: float
    rel_deadline: float


@dataclass
class Workload:
    tasks: list[Task]


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
