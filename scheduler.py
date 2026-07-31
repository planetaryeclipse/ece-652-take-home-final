from typing import Any

import numpy as np

from dataclasses import dataclass

from workload import Task, Workload

SCHEDULER_TIME_PRECISION = 3


@dataclass
class TaskInstance:
    task: Task  # originating task of the instance

    release: float  # release time
    deadline: float  # absolute deadline
    remaining_exec_time: float  # time remaining in execution

    start: float | None = None  # start time
    preempts: list[float] = []  # times when preempted
    resumes: list[float] = []  # times when resume execution
    finish: float | None = None  # finish time


def at_task_release(
    task: Task,
    time: float,
    precision: int = SCHEDULER_TIME_PRECISION,
) -> bool:
    """checks whether the current time should trigger a release of the provided task"""

    # due to floating point round off need this manual computation of the remainder
    remainder = round(time - round(time / task.period) * task.period, precision)
    return remainder == 0.0


def release_tasks(
    workload: Workload,
    curr_time: float,
    created_insts: list[TaskInstance],
    pending_insts: list[TaskInstance],
    precision: int = SCHEDULER_TIME_PRECISION,
):
    """check current time against task periods and release new instances if needed"""
    for task in workload.tasks:
        if at_task_release(task, curr_time, precision=precision):
            inst = TaskInstance(
                task=task,
                release=curr_time,
                deadline=curr_time + task.rel_deadline,
                remaining_exec_time=task.exec_time,
            )
            created_insts.append(inst)
            pending_insts.append(inst)


def get_highest_priority_task(pending_insts: list[TaskInstance]) -> TaskInstance:
    """gets the highest priority task based on deadline based on deadline monotonic scheduling"""
    curr_inst_earliest_deadline = None
    for inst in pending_insts:
        if (
            curr_inst_earliest_deadline is None
            or inst.deadline < curr_inst_earliest_deadline.deadline
        ):
            curr_inst_earliest_deadline = inst
    assert curr_inst_earliest_deadline is not None  # sanity check
    return curr_inst_earliest_deadline


def get_time_to_next_schedule_event(
    workload: Workload,
    running_inst: TaskInstance,
    curr_time: float,
    precision: int = SCHEDULER_TIME_PRECISION,
) -> float:
    """gests the time until the next scheduling decision must be made"""
    # stepping through all levels of precision would be very slow so instead determine when the next event will
    # actually occur (either tasks are released or the current task has finished execution)

    time_to_next_task_releases = [
        round(np.ceil(curr_time / task.period) * task.period - curr_time, precision)
        for task in workload.tasks
    ]
    time_to_next_schedule_event = min(
        running_inst.remaining_exec_time if running_inst is not None else np.inf,
        *time_to_next_task_releases,
    )

    return time_to_next_schedule_event


def dm_schedule(
    workload: Workload, precision: int = SCHEDULER_TIME_PRECISION
) -> Schedule | None:
    created_insts: list[TaskInstance] = []
    pending_insts: list[TaskInstance] = []

    running_inst: TaskInstance | None = None
    curr_time = 0.0

    while True:
        # check to see whether any instances have violated their deadlines
        for inst in pending_insts:
            if curr_time > inst.deadline:
                return None  # indicating a failed result

        # check whether currently executing task (if exists) is currently running
        if running_inst is not None and running_inst.remaining_exec_time == 0.0:
            running_inst.finish = curr_time
            running_inst = None

        release_tasks(
            workload,
            curr_time,
            created_insts,
            pending_insts,
            precision=precision,
        )
        highest_priority_inst = get_highest_priority_task(pending_insts)

        # checks to see if a preemption is necessary
        if running_inst is not highest_priority_inst and running_inst is not None:
            running_inst.preempts.append(curr_time)

        # handles starting or restarting the task instance
        running_inst = highest_priority_inst
        if running_inst.start is None:  # cold start of a task instance
            running_inst.start = curr_time
        else:
            running_inst.resumes.append(curr_time)

        # simulates the increase in time and exection of the task
        time_to_next_schedule_event = get_time_to_next_schedule_event(
            workload,
            running_inst,
            curr_time,
            precision=precision,
        )
        curr_time = round(curr_time + time_to_next_schedule_event, precision)
        if running_inst is not None:
            running_inst.remaining_exec_time = round(
                running_inst.remaining_exec_time - time_to_next_schedule_event,
                precision,
            )

        # testing break
        if curr_time > 200.0:
            break
