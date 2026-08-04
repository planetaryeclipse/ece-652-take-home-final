import numpy as np

from dataclasses import dataclass, field

from workload import Task, Workload

TIME_PRECISION = 3
MIN_TIMESTEP = 1e-3

# data structures


@dataclass
class TaskInstance:
    task: Task  # originating task of the instance

    release: float  # release time
    deadline: float  # absolute deadline
    remaining_exec_time: float  # time remaining in execution

    start: float | None = None  # start time
    preempts: list[float] = field(default_factory=list)  # times when preempted
    resumes: list[float] = field(default_factory=list)  # times when resume execution
    finish: float | None = None  # finish time


# hyperperiod checker


def get_inst_at_time(insts: list[TaskInstance], time: float) -> TaskInstance:
    for inst in insts:
        if inst.start is None or inst.finish is None:
            continue

        starts = [inst.start, *inst.resumes]
        stops = [*inst.preempts, inst.finish]

        for start, stop in zip(starts, stops):
            if start <= time and time <= stop:
                return inst
    raise ValueError(f"unable to find instance at specified time {time}")


def get_inst_exec_end(inst: TaskInstance, time: float):
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
        first_hp_inst = get_inst_at_time(insts, first_hyperperiod_release_time)
        next_hp_inst = get_inst_at_time(insts, next_possible_hyperperiod_release_time)

        insts_in_first_hp = set([first_hp_inst])
        insts_in_next_hp = set([next_hp_inst])

        hp_rel_time = 0.0  # time within the hyperperiod
        while True:
            if first_hp_inst.task is not next_hp_inst.task:
                return None

            # finds the stop of execution (either preempted or finishes) for the tasks in each hyperperiod
            first_exec_end = get_inst_exec_end(
                first_hp_inst,
                hp_rel_time + first_hyperperiod_release_time,
            )
            next_exec_end = get_inst_exec_end(
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
            first_hp_inst = get_inst_at_time(insts, hp_rel_time + first_hyperperiod_release_time)
            next_hp_inst = get_inst_at_time(insts, hp_rel_time + next_possible_hyperperiod_release_time)

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


def get_highest_priority_task(pending_insts: list[TaskInstance]) -> TaskInstance | None:
    """gets the highest priority task based on deadline based on deadline monotonic scheduling"""
    inst_earliest_deadline = None
    return


def get_time_to_next_schedule_event(
    workload: Workload,
    running_inst: TaskInstance | None,
    curr_time: float,
) -> float:
    """gets the time until the next scheduling decision must be made"""
    # stepping through all levels of precision would be very slow so instead determine when the next event will
    # actually occur (either tasks are released or the current task has finished execution)

    time_to_next_task_releases = [
        round(np.ceil((curr_time + MIN_TIMESTEP) / task.period) * task.period - curr_time) for task in workload.tasks
    ]
    time_to_next_schedule_event = min(
        running_inst.remaining_exec_time if running_inst is not None else np.inf,
        *time_to_next_task_releases,
    )

    return time_to_next_schedule_event


@dataclass
class Schedule:
    insts: list[TaskInstance]


@dataclass
class AdvancingSchedule:
    time: float = 0.0
    running_inst: TaskInstance | None = None
    created_insts: list[TaskInstance] = field(default_factory=list)
    pending_insts: list[TaskInstance] = field(default_factory=list)
    possible_hp_releases: list[float] = field(default_factory=list)


def dm_make_scheduling_decision(
    workload: Workload,
    schedule: AdvancingSchedule,
) -> bool:
    # check to see whether any instances have violated their deadlines
    for inst in schedule.pending_insts:
        if schedule.time > inst.deadline:
            return False  # failed

    # check whether currently executing task (if exists) is currently running
    if schedule.running_inst is not None and schedule.running_inst.remaining_exec_time == 0.0:
        schedule.pending_insts.remove(schedule.running_inst)
        schedule.running_inst.finish = schedule.time
        schedule.running_inst = None

    all_released = release_tasks(workload, schedule.time, schedule.created_insts, schedule.pending_insts)
    if all_released:
        schedule.possible_hp_releases.append(schedule.time)
    priority_inst = min(
        schedule.pending_insts,
        key=lambda inst: inst.deadline,
        default=None,  # idle if none pending
    )

    # checks to see if a preemption is necessary
    if schedule.running_inst is not priority_inst and schedule.running_inst is not None:
        schedule.running_inst.preempts.append(schedule.time)

    # handles starting or restarting the task instance
    schedule.running_inst = priority_inst
    if schedule.running_inst is not None:
        if schedule.running_inst.start is None:  # cold start of a task instance
            schedule.running_inst.start = schedule.time
        else:
            schedule.running_inst.resumes.append(schedule.time)

    return True  # no failure reported


def dm_advance_exec(workload: Workload, schedule: AdvancingSchedule):
    # simulates the increase in time and execution of the task (whether the task has finished will be determined )
    time_to_next_schedule_event = get_time_to_next_schedule_event(
        workload,
        schedule.running_inst,
        schedule.time,
    )
    print(f"time_to_next_schedule_event: {time_to_next_schedule_event}")
    schedule.time = round(schedule.time + time_to_next_schedule_event)
    if schedule.running_inst is not None:
        schedule.running_inst.remaining_exec_time = round(
            schedule.running_inst.remaining_exec_time - time_to_next_schedule_event,
        )


def dm_schedule(workload: Workload) -> Schedule | None:
    schedule = AdvancingSchedule()
    while True:
        num_all_released = len(schedule.possible_hp_releases)
        result = dm_make_scheduling_decision(workload, schedule)
        if not result:
            return None  # unschedulable

        # check if a hyperperiod can be ascertained if a new all release point has been identified
        upd_num_all_released = len(schedule.possible_hp_releases)
        if upd_num_all_released > num_all_released and upd_num_all_released > 2:
            hyperperiod_insts = find_hyperperiod_schedule(
                schedule.created_insts,
                schedule.possible_hp_releases,
            )
            if hyperperiod_insts is not None:
                return Schedule(hyperperiod_insts)

        dm_advance_exec(workload, schedule)


def count_task_preemptions(workload: Workload, schedule: Schedule) -> dict[Task, int]:
    num_preempts = {task: 0 for task in workload.tasks}

    insts = schedule.insts.copy()
    while len(insts) > 0:
        inst = insts.pop()
        num_preempts[inst.task] += 1

    return num_preempts
