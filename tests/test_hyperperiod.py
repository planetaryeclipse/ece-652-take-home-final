from pytest import approx

from scheduler import (
    AdvancingSchedule,
    dm_advance_exec,
    dm_make_scheduling_decision,
    dm_schedule,
    get_hyperperiod_schedule,
)
from workload import Task, Workload


def test_single_task_manual():
    workload = Workload([Task(exec_time=1, period=3, rel_deadline=3)])
    schedule = AdvancingSchedule()

    # only able to detect a hyperperiod when 2 full cycles have been achieved plus one more scheduling decision to
    # release more tasks (for simplicity and clarity of source implementation)

    # INST -----------------------------------------------------------
    assert dm_make_scheduling_decision(workload, schedule)
    dm_advance_exec(workload, schedule)

    assert get_hyperperiod_schedule(schedule) is None

    # IDLE -----------------------------------------------------------
    assert dm_make_scheduling_decision(workload, schedule)
    dm_advance_exec(workload, schedule)

    assert get_hyperperiod_schedule(schedule) is None

    # INST -----------------------------------------------------------

    assert dm_make_scheduling_decision(workload, schedule)
    dm_advance_exec(workload, schedule)

    assert get_hyperperiod_schedule(schedule) is None  # still not 2 cycles

    # IDLE -----------------------------------------------------------
    assert dm_make_scheduling_decision(workload, schedule)
    dm_advance_exec(workload, schedule)

    assert get_hyperperiod_schedule(schedule) is None

    # LAST SCHEDULING CALL -------------------------------------------
    assert dm_make_scheduling_decision(workload, schedule)

    hyperperiod_schedule = get_hyperperiod_schedule(schedule)
    assert hyperperiod_schedule is not None
    assert len(hyperperiod_schedule) == 1

    inst = hyperperiod_schedule[0]
    assert approx(inst.release) == 0.0
    assert approx(inst.start) == 0.0
    assert approx(inst.finish) == 1.0
    assert approx(inst.remaining_exec_time) == 0.0


def test_single_task():
    workload = Workload([Task(exec_time=1, period=3, rel_deadline=3)])
    hyperperiod_schedule = dm_schedule(workload)

    assert hyperperiod_schedule is not None
    assert len(hyperperiod_schedule.insts) == 1

    inst = hyperperiod_schedule.insts[0]
    assert approx(inst.release) == 0.0
    assert approx(inst.start) == 0.0
    assert approx(inst.finish) == 1.0
    assert approx(inst.remaining_exec_time) == 0.0
