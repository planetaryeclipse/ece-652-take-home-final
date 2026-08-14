from pytest import approx

from scheduler import (
    AdvancingSchedule,
    Task,
    Workload,
    dm_advance_exec,
    dm_make_scheduling_decision,
    dm_schedule,
    get_hyperperiod_schedule,
)


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

    result = get_hyperperiod_schedule(schedule)
    assert result is not None
    hyperperiod_insts, hyperperiod = result
    assert len(hyperperiod_insts) == 1

    inst = hyperperiod_insts[0]
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


def test_precision_single_task():
    workload = Workload([Task(exec_time=0.234, period=0.789, rel_deadline=3)])
    hyperperiod_schedule = dm_schedule(workload)

    assert hyperperiod_schedule is not None
    assert len(hyperperiod_schedule.insts) == 1

    inst = hyperperiod_schedule.insts[0]
    assert approx(inst.release) == 0.0
    assert approx(inst.start) == 0.0
    assert approx(inst.finish) == 0.234
    assert approx(inst.remaining_exec_time) == 0.0


def test_precision_two_tasks_same_period():
    task_1 = Task(0.123, 0.789, 0.789)
    task_2 = Task(0.666, 0.789, 0.789)
    workload = Workload([task_1, task_2])
    schedule = dm_schedule(workload)

    assert schedule is not None
    assert len(schedule.insts) == 2

    t1_inst, t2_inst = schedule.insts

    assert approx(t1_inst.release) == 0.0
    assert approx(t1_inst.start) == 0.0
    assert approx(t1_inst.finish) == 0.123
    assert approx(t1_inst.remaining_exec_time) == 0.0

    assert approx(t2_inst.release) == 0.0
    assert approx(t2_inst.start) == 0.123
    assert approx(t2_inst.finish) == 0.789
    assert approx(t2_inst.remaining_exec_time) == 0.0


def test_precision_three_tasks_same_period():
    task_1 = Task(0.123, 0.890, 0.890)
    task_2 = Task(0.234, 0.890, 0.890)
    task_3 = Task(0.345, 0.890, 0.890)  # has following idle period
    workload = Workload([task_1, task_2, task_3])
    schedule = dm_schedule(workload)

    assert schedule is not None
    assert len(schedule.insts) == 3

    t1_inst, t2_inst, t3_inst = schedule.insts

    assert approx(t1_inst.release) == 0.0
    assert approx(t1_inst.start) == 0.0
    assert approx(t1_inst.finish) == 0.123
    assert approx(t1_inst.remaining_exec_time) == 0.0

    assert approx(t2_inst.release) == 0.0
    assert approx(t2_inst.start) == 0.123
    assert approx(t2_inst.finish) == 0.123 + 0.234
    assert approx(t2_inst.remaining_exec_time) == 0.0

    assert approx(t3_inst.release) == 0.0
    assert approx(t3_inst.start) == 0.123 + 0.234
    assert approx(t3_inst.finish) == 0.123 + 0.234 + 0.345
    assert approx(t3_inst.remaining_exec_time) == 0.0
