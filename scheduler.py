import numpy as np

import time

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


# hyperperiod checker


def get_next_resume_time_from_idle(insts: list[TaskInstance], time: float) -> float | None:
    assert get_inst_at_time(insts, time) is None  # sanity chech

    min_rel_start_time = None
    for inst in insts:
        if inst.start is not None:
            if time > inst.start:
                continue

            rel_start_time = inst.start - time
            if min_rel_start_time is None:
                min_rel_start_time = rel_start_time
            else:
                min_rel_start_time = min(min_rel_start_time, rel_start_time)

    if min_rel_start_time is not None:
        return min_rel_start_time + time
    return None


def get_inst_at_time(insts: list[TaskInstance], time: float) -> TaskInstance | None:
    # print(f"get inst @ time: {time}")
    # for inst in insts:
    #     print(f"\tinst: {inst}")
    for inst in insts:
        if inst.start is None:
            continue
        elif len(inst.resumes) == 0 and inst.finish is None:
            # edge case for if a scheduling decision was just made but no execution (so obviously no preemptions or even
            # a finish time has been recorded for the job instance)
            if inst.start == time:
                return inst
        else:
            starts = [inst.start, *inst.resumes[:-1]]
            stops = [*inst.preempts]
            if inst.finish is not None:
                if len(inst.resumes) != 0:
                    starts.append(inst.resumes[-1])
                stops.append(inst.finish)

            for start, stop in zip(starts, stops):
                # ensure that instances that start/resume at this time take precendence over finishing
                if start <= time and time < stop:
                    return inst
    return None  # no active instance (idle period)


def get_inst_exec_end(inst: TaskInstance, time: float):
    assert inst.start is not None  # typing assistance
    assert inst.finish is not None

    starts = [inst.start, *inst.resumes]
    stops = [*inst.preempts, inst.finish]

    # print()
    # print(f"time: {time}")
    for start, stop in zip(starts, stops):
        # print(f"start: {start}, stop: {stop}")

        if start <= time and time < stop:
            # print(f"returning stop time: {stop}")
            return stop
    raise RuntimeError()


def check_hp_insts_finished(
    hp_rel_time: float,
    first_hp_rel_time: float,
    next_possible_hp_rel_time: float,
    insts_in_first_hp: list[TaskInstance],
    insts_in_next_hp: list[TaskInstance],
) -> bool:
    for inst in insts_in_first_hp:
        assert inst.finish is not None
        if round(hp_rel_time + first_hp_rel_time, TIME_PRECISION) >= inst.finish:
            return False
    for inst in insts_in_next_hp:
        assert inst.finish is not None
        if round(hp_rel_time + next_possible_hp_rel_time, TIME_PRECISION) >= inst.finish:
            return False
    return True


def get_hyperperiod_schedule(schedule: AdvancingSchedule) -> list[TaskInstance] | None:
    if len(schedule.possible_hp_releases) < 2:
        return None

    first_hp_rel_time = schedule.possible_hp_releases[0]  # technically always 0
    for next_possible_hp_rel_time in schedule.possible_hp_releases[1:]:
        release_delta = next_possible_hp_rel_time - first_hp_rel_time

        # gets the running task instances at the start of the assumed hyperperiods
        first_hp_inst = get_inst_at_time(schedule.created_insts, first_hp_rel_time)
        next_hp_inst = get_inst_at_time(schedule.created_insts, next_possible_hp_rel_time)

        # print(f"first_hp_inst: {first_hp_inst}")
        # print(f"next_hp_inst: {next_hp_inst}")

        assert isinstance(first_hp_inst, TaskInstance)
        assert isinstance(next_hp_inst, TaskInstance)

        insts_in_first_hp: list[TaskInstance] = [first_hp_inst]
        insts_in_next_hp: list[TaskInstance] = [next_hp_inst]

        hp_rel_time = 0.0  # time within the hyperperiod
        while True:
            # print(f"hp_rel_time: {hp_rel_time}")

            if first_hp_inst is None and next_hp_inst is None:
                # print("in IDLE")

                # print(f"time1: {hp_rel_time + first_hp_rel_time}")
                # print(f"time2: {hp_rel_time + next_possible_hp_rel_time}")
                first_resume_time = get_next_resume_time_from_idle(
                    schedule.created_insts, hp_rel_time + first_hp_rel_time
                )
                next_resume_time = get_next_resume_time_from_idle(
                    schedule.created_insts, hp_rel_time + next_possible_hp_rel_time
                )

                if first_resume_time is not None and next_resume_time is not None:

                    if round(next_resume_time - first_resume_time - release_delta, TIME_PRECISION) != 0.0:
                        break  # idle times must be the same to be valid

                    hp_rel_time = first_resume_time
                    if round(hp_rel_time, TIME_PRECISION) == release_delta:

                        for inst in insts_in_first_hp:
                            assert inst.finish is not None
                            if round(hp_rel_time + first_hp_rel_time, TIME_PRECISION) >= inst.finish:
                                break
                        for inst in insts_in_next_hp:
                            assert inst.finish is not None
                            if round(hp_rel_time + next_possible_hp_rel_time, TIME_PRECISION) >= inst.finish:
                                break

                        # at this point the execution of the hyperperiod is known so return it as a separate schedule (note that
                        # this returns immediately to ensure no integer multiples of hyperperiod are returned)
                        return list(insts_in_first_hp)
                else:
                    # first_hp_inst being None is unreachable but
                    break  # invalid

                pass
            elif first_hp_inst is not None and next_hp_inst is not None:
                # print("inside NON-IDLE")

                if first_hp_inst.task is not next_hp_inst.task:
                    # print(f"breaking due to wrong task, first: {first_hp_inst.task}, next: {next_hp_inst.task}")
                    break  # originating task must match
                elif next_hp_inst.finish is None:
                    # print(f"right not finished")
                    # if task in next hyperperiod unfinished at this point in iteration then the hyperperiod has not yet
                    # been reached for this particular workflow
                    return None

                # finds the stop of execution (either preempted or finishes) for the tasks in each hyperperiod
                first_exec_end = get_inst_exec_end(first_hp_inst, hp_rel_time + first_hp_rel_time)
                next_exec_end = get_inst_exec_end(next_hp_inst, hp_rel_time + next_possible_hp_rel_time)

                # print(f"first_exec_end: {first_exec_end}, next_exec_end: {next_exec_end}")

                # check whether execution terminates at differing times
                if round(next_exec_end - first_exec_end, TIME_PRECISION) != release_delta:
                    break  # continue on to check remaining possibilities

                hp_rel_time = first_exec_end
                # print(f"upd hp_rel_time: {hp_rel_time}")

                # check whether the first hyperperiod has reached the release of the next hyperperiod
                if round(hp_rel_time, TIME_PRECISION) == release_delta:
                    # so far everything matches in terms of execution but we must also ensure that all task instances within
                    # each prospective hyperperiod have finished to avoid any edge cases

                    for inst in insts_in_first_hp:
                        assert inst.finish is not None
                        if round(hp_rel_time + first_hp_rel_time, TIME_PRECISION) >= inst.finish:
                            break
                    for inst in insts_in_next_hp:
                        assert inst.finish is not None
                        if round(hp_rel_time + next_possible_hp_rel_time, TIME_PRECISION) >= inst.finish:
                            break

                    # at this point the execution of the hyperperiod is known so return it as a separate schedule (note that
                    # this returns immediately to ensure no integer multiples of hyperperiod are returned)
                    return list(insts_in_first_hp)
            else:
                return None  # one hyperperiod has a running task instance and the othre is idle

            # gets the new tasks that have started
            first_hp_inst = get_inst_at_time(schedule.created_insts, hp_rel_time + first_hp_rel_time)
            next_hp_inst = get_inst_at_time(schedule.created_insts, hp_rel_time + next_possible_hp_rel_time)

            if first_hp_inst is not None and first_hp_inst not in insts_in_first_hp:
                insts_in_first_hp.append(first_hp_inst)
            if next_hp_inst is not None and next_hp_inst not in insts_in_next_hp:
                insts_in_next_hp.append(next_hp_inst)

            # print("advancing check...")

        # time.sleep(0.4)
        # print()
        # print("starting next check...")
        # print()

    # unable to ascertain a hyperperiod schedule from the provided schedule
    # print("no hyperperiod detected")
    return None


# scheduler


def at_task_release(
    task: Task,
    time: float,
) -> bool:
    """checks whether the current time should trigger a release of the provided task"""

    # due to floating point round off need this manual computation of the remainder
    remainder = round(
        time
        - np.floor(
            time / task.period,
        )
        * task.period,
        TIME_PRECISION,
    )

    # print(f"task: {task}, time: {time}, remainder: {remainder}")

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


def get_time_to_next_schedule_event(
    workload: Workload,
    running_inst: TaskInstance | None,
    curr_time: float,
) -> float:
    """gets the time until the next scheduling decision must be made"""
    # stepping through all levels of precision would be very slow so instead determine when the next event will
    # actually occur (either tasks are released or the current task has finished execution)

    # print(f"curr remaining_exec_time: {running_inst.remaining_exec_time if running_inst is not None else None}")

    time_to_next_task_releases = [
        round(np.ceil((curr_time + MIN_TIMESTEP) / task.period) * task.period - curr_time, TIME_PRECISION)
        for task in workload.tasks
    ]

    time_to_next_schedule_event = min(
        running_inst.remaining_exec_time if running_inst is not None else np.inf,
        *time_to_next_task_releases,
    )

    # print(f"time_to_next_task_release: {time_to_next_task_releases}")
    # print(f"time_to_next_schedule_event: {time_to_next_schedule_event}")

    return time_to_next_schedule_event


def dm_make_scheduling_decision(
    workload: Workload,
    schedule: AdvancingSchedule,
) -> bool:
    # must check whether any instances have failed before removing them from pending if finished as this ensures that
    # when the current task ends this condition is checked immediately and correctly assess whether the termination
    # occurred after the specified deadline
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

    # for inst in schedule.pending_insts:
    #     print(f"pending inst: {inst}")

    priority_inst = min(
        schedule.pending_insts,
        key=lambda inst: inst.task.rel_deadline,  # EDF if inst.deadline
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

    # print(f"time_to_next_schedule_event: {time_to_next_schedule_event}")

    schedule.time = round(schedule.time + time_to_next_schedule_event, TIME_PRECISION)
    if schedule.running_inst is not None:
        schedule.running_inst.remaining_exec_time = round(
            schedule.running_inst.remaining_exec_time - time_to_next_schedule_event, TIME_PRECISION
        )


def dm_schedule(workload: Workload) -> Schedule | None:
    schedule = AdvancingSchedule()
    while True:
        # print(
        #     f"@ start schedule time: {schedule.time}, inst id: {workload.tasks.index(schedule.running_inst.task) if schedule.running_inst is not None else None}"
        # )

        num_all_released = len(schedule.possible_hp_releases)
        result = dm_make_scheduling_decision(workload, schedule)
        if not result:
            return None  # unschedulable

        # check if a hyperperiod can be ascertained if a new all release point has been identified
        upd_num_all_released = len(schedule.possible_hp_releases)
        if upd_num_all_released > num_all_released and upd_num_all_released > 2:
            hyperperiod_insts = get_hyperperiod_schedule(schedule)
            if hyperperiod_insts is not None:
                return Schedule(hyperperiod_insts)

        # print(
        #     f"@ chosen inst id: {workload.tasks.index(schedule.running_inst.task) if schedule.running_inst is not None else None}"
        # )

        # print("advancing...")
        dm_advance_exec(workload, schedule)

        # print()


def count_task_preemptions(workload: Workload, schedule: Schedule) -> list[int]:
    num_preempts = [0 for task in workload.tasks]
    insts = schedule.insts.copy()
    while len(insts) > 0:
        inst = insts.pop()
        idx = workload.tasks.index(inst.task)
        num_preempts[idx] += len(inst.preempts)
    return num_preempts
