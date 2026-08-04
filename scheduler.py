import numpy as np

from dataclasses import dataclass

from workload import Task, Workload

TIME_PRECISION = 3

# data structures


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


# hyperperiod checker


def find_inst_at_time(insts: list[TaskInstance], time: float) -> TaskInstance:
    for inst in insts:
        if inst.start is None or inst.finish is None:
            continue

        starts = [inst.start, *inst.resumes]
        stops = [*inst.preempts, inst.finish]

        for start, stop in zip(starts, stops):
            if start <= time and time <= stop:
                return inst
    raise ValueError(f"unable to find instance at specified time {time}")


def get_end_of_current_inst_exec(inst: TaskInstance, time: float):
    assert inst.start is not None  # typing assistance
    assert inst.finish is not None

    starts = [inst.start, *inst.resumes]
    stops = [*inst.preempts, inst.finish]

    for start, stop in zip(starts, stops):
        if round(time - start, TIME_PRECISION) >= 0.0 and round(stop - time, TIME_PRECISION) >= 0.0:
            return stop
    raise RuntimeError()


def find_hyperperiod_schedule(
    insts: list[TaskInstance],
    all_release_times: list[float],
) -> list[TaskInstance] | None:
    if len(all_release_times) < 2:
        return None

    first_hyperperiod_release_time = all_release_times[0]  # technically always 0
    for next_possible_hyperperiod_release_time in all_release_times[1:]:

        release_delta = next_possible_hyperperiod_release_time - first_hyperperiod_release_time

        # gets the running task instances at the start of the assumed hyperperiods
        first_hp_inst = find_inst_at_time(insts, first_hyperperiod_release_time)
        next_hp_inst = find_inst_at_time(insts, next_possible_hyperperiod_release_time)

        insts_in_first_hp = set([first_hp_inst])
        insts_in_next_hp = set([next_hp_inst])

        hp_rel_time = 0.0  # time within the hyperperiod
        while True:
            if first_hp_inst.task is not next_hp_inst.task:
                return None

            # finds the stop of execution (either preempted or finishes) for the tasks in each hyperperiod
            first_exec_end = get_end_of_current_inst_exec(
                first_hp_inst,
                hp_rel_time + first_hyperperiod_release_time,
            )
            next_exec_end = get_end_of_current_inst_exec(
                next_hp_inst,
                hp_rel_time + next_possible_hyperperiod_release_time,
            )

            # check whether execution terminates at differing times
            if round(first_exec_end - next_exec_end, TIME_PRECISION) != release_delta:
                break  # continue on to check remaining possibilities

            hp_rel_time = first_exec_end

            # check whether the first hyperperiod has reached the release of the next hyperperiod
            if round(hp_rel_time, TIME_PRECISION) == release_delta:
                # so far everything matches in terms of execution but we must also ensure that all task instances within
                # each prospective hyperperiod have finished to avoid any edge cases

                for inst in insts_in_first_hp:
                    assert inst.finish is not None
                    if round(hp_rel_time + first_hyperperiod_release_time, TIME_PRECISION) >= inst.finish:
                        break
                for inst in insts_in_next_hp:
                    assert inst.finish is not None
                    if round(hp_rel_time + next_possible_hyperperiod_release_time, TIME_PRECISION) >= inst.finish:
                        break

                # at this point the execution of the hyperperiod is known so return it as a separate schedule (note that
                # this returns immediately to ensure no integer multiples of hyperperiod are returned)
                return list(insts_in_first_hp)

            # gets the new tasks that have started
            first_hp_inst = find_inst_at_time(insts, hp_rel_time + first_hyperperiod_release_time)
            next_hp_inst = find_inst_at_time(insts, hp_rel_time + next_possible_hyperperiod_release_time)

            insts_in_first_hp.add(first_hp_inst)
            insts_in_next_hp.add(next_hp_inst)

            # we have strayed too far and the schedule remains unfinished, so obvously we have not hit the hyperperiod
            if next_hp_inst.finish is None:
                break

    # unable to ascertain a hyperperiod schedule from the provided schedule
    return None


# scheduler


def at_task_release(
    task: Task,
    time: float,
) -> bool:
    """checks whether the current time should trigger a release of the provided task"""

    # due to floating point round off need this manual computation of the remainder
    remainder = round(time - round(time / task.period) * task.period)
    return remainder == 0.0


def release_tasks(
    workload: Workload,
    curr_time: float,
    created_insts: list[TaskInstance],
    pending_insts: list[TaskInstance],
) -> bool:
    """check current time against task periods and release new instances if needed"""
    all_released = True
    for task in workload.tasks:
        if at_task_release(task, curr_time):
            inst = TaskInstance(
                task=task,
                release=curr_time,
                deadline=curr_time + task.rel_deadline,
                remaining_exec_time=task.exec_time,
            )
            created_insts.append(inst)
            pending_insts.append(inst)
        else:
            all_released = False
    return all_released


def get_highest_priority_task(pending_insts: list[TaskInstance]) -> TaskInstance:
    """gets the highest priority task based on deadline based on deadline monotonic scheduling"""
    curr_inst_earliest_deadline = None
    for inst in pending_insts:
        if curr_inst_earliest_deadline is None or inst.deadline < curr_inst_earliest_deadline.deadline:
            curr_inst_earliest_deadline = inst
    assert curr_inst_earliest_deadline is not None  # sanity check
    return curr_inst_earliest_deadline


def get_time_to_next_schedule_event(
    workload: Workload,
    running_inst: TaskInstance,
    curr_time: float,
    precision: int = TIME_PRECISION,
) -> float:
    """gests the time until the next scheduling decision must be made"""
    # stepping through all levels of precision would be very slow so instead determine when the next event will
    # actually occur (either tasks are released or the current task has finished execution)

    time_to_next_task_releases = [
        round(np.ceil(curr_time / task.period) * task.period - curr_time, precision) for task in workload.tasks
    ]
    time_to_next_schedule_event = min(
        running_inst.remaining_exec_time if running_inst is not None else np.inf,
        *time_to_next_task_releases,
    )

    return time_to_next_schedule_event


@dataclass
class Schedule:
    workload: Workload
    insts: list[TaskInstance]


def dm_schedule(workload: Workload) -> list[TaskInstance] | None:
    created_insts: list[TaskInstance] = []
    pending_insts: list[TaskInstance] = []
    all_release_times: list[float] = [0.0]

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

        all_released = release_tasks(workload, curr_time, created_insts, pending_insts)
        if all_released:
            # check whether a hyperperiod is found before adding the release time as nominally this would be a complete
            # second hyperperiod (to which adding another task instance would add an unncessary case)
            if len(all_release_times) >= 2:
                hyperperiod_schedule = find_hyperperiod_schedule(created_insts, all_release_times)
                if hyperperiod_schedule is not None:
                    return hyperperiod_schedule
            all_release_times.append(curr_time)
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
        )
        curr_time = round(curr_time + time_to_next_schedule_event)
        if running_inst is not None:
            running_inst.remaining_exec_time = round(
                running_inst.remaining_exec_time - time_to_next_schedule_event,
            )


def count_task_preemptions(workload: Workload, schedule: list[TaskInstance]) -> dict[Task, int]:
    num_preempts = {task: 0 for task in workload.tasks}

    schedule = schedule.copy()
    while len(schedule) > 0:
        inst = schedule.pop()
        num_preempts[inst.task] += 1

    return num_preempts
