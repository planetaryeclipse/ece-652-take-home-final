from scheduler import AdvancingSchedule, dm_advance_exec, dm_make_scheduling_decision
from workload import Task, Workload
from pytest import approx


def test_single_task():
    workload = Workload([Task(exec_time=1, period=3, rel_deadline=3)])
    schedule = AdvancingSchedule()

    assert len(schedule.created_insts) == 0

    # FIRST INSTANCE ------------------------------------------------
    # ensure that task is created and no execution is performed
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.created_insts) == 1
    inst_1 = schedule.created_insts[0]

    assert schedule.running_inst is inst_1
    assert approx(schedule.time) == 0.0
    assert approx(inst_1.remaining_exec_time) == 1.0

    # advance execution to next event
    dm_advance_exec(workload, schedule)
    assert schedule.running_inst is inst_1
    assert approx(schedule.time) == 1.0
    assert approx(inst_1.remaining_exec_time) == 0.0

    # IDLE ----------------------------------------------------------

    # no tasks created so must advance past with no updates
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.created_insts) == 1

    assert schedule.running_inst is None
    assert approx(schedule.time) == 1.0
    assert approx(inst_1.remaining_exec_time) == 0.0

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 3.0
    assert approx(inst_1.remaining_exec_time) == 0.0

    # SECOND INSTANCE -----------------------------------------------
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.created_insts) == 2
    inst_2 = schedule.created_insts[1]

    assert schedule.running_inst is inst_2
    assert approx(schedule.time) == 3.0
    assert approx(inst_1.remaining_exec_time) == 0.0
    assert approx(inst_2.remaining_exec_time) == 1.0

    dm_advance_exec(workload, schedule)
    assert schedule.running_inst is inst_2
    assert approx(schedule.time) == 4.0
    assert approx(inst_1.remaining_exec_time) == 0.0
    assert approx(inst_2.remaining_exec_time) == 0.0
