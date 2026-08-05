from pytest import approx

from scheduler import AdvancingSchedule, dm_advance_exec, dm_make_scheduling_decision
from workload import Task, Workload


def test_single_task_manual():
    workload = Workload([Task(exec_time=1, period=3, rel_deadline=3)])
    schedule = AdvancingSchedule()

    assert len(schedule.created_insts) == 0

    # first instance
    # ensure that task is created and no execution is performed
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.created_insts) == 1
    inst_1 = schedule.created_insts[0]

    assert schedule.running_inst is inst_1
    assert approx(schedule.time) == 0.0
    assert approx(inst_1.release) == 0.0
    assert approx(inst_1.start) == 0.0
    assert approx(inst_1.remaining_exec_time) == 1.0

    # advance execution to next event
    dm_advance_exec(workload, schedule)
    assert schedule.running_inst is inst_1
    assert approx(schedule.time) == 1.0
    assert approx(inst_1.release) == 0.0
    assert approx(inst_1.start) == 0.0
    assert approx(inst_1.remaining_exec_time) == 0.0

    # idle
    # no tasks created so must advance past with no updates
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.created_insts) == 1

    assert schedule.running_inst is None
    assert approx(schedule.time) == 1.0
    assert approx(inst_1.release) == 0.0
    assert approx(inst_1.start) == 0.0
    assert approx(inst_1.remaining_exec_time) == 0.0

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 3.0
    assert approx(inst_1.release) == 0.0
    assert approx(inst_1.start) == 0.0
    assert approx(inst_1.remaining_exec_time) == 0.0

    # second instance
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.created_insts) == 2
    inst_2 = schedule.created_insts[1]

    assert schedule.running_inst is inst_2
    assert approx(schedule.time) == 3.0
    assert approx(inst_1.release) == 0.0
    assert approx(inst_1.start) == 0.0
    assert approx(inst_1.remaining_exec_time) == 0.0
    assert approx(inst_2.release) == 3.0
    assert approx(inst_2.start) == 3.0
    assert approx(inst_2.remaining_exec_time) == 1.0

    dm_advance_exec(workload, schedule)
    assert schedule.running_inst is inst_2
    assert approx(schedule.time) == 4.0
    assert approx(inst_1.release) == 0.0
    assert approx(inst_1.start) == 0.0
    assert approx(inst_1.remaining_exec_time) == 0.0
    assert approx(inst_2.release) == 3.0
    assert approx(inst_2.start) == 3.0
    assert approx(inst_2.remaining_exec_time) == 0.0


def test_multi_task_manual():
    task_1 = Task(1, 3, 3)
    task_2 = Task(2, 4, 5)
    workload = Workload([task_1, task_2])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # both T1 and T2
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1  # T1 lowest period

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 1.0  # end of execution of T1

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # only T2
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2  # only remaining

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 3.0

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # T1 refreshed
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 4.0

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # T2 refreshed
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 6.0

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # T1 refeshed
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 7.0  # after execution of T1

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 0  # no tasks refreshed
    assert schedule.running_inst is None

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 8.0  # ready to be refreshed

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # T2 refreshed
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 9.0  # preemption by T1

    task_2_inst_3 = schedule.running_inst  # preempt after next scheduling

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # T2 still also pending
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    assert len(task_2_inst_3.preempts) == 1  # scheduler decision triggers preemption
    assert approx(task_2_inst_3.preempts[0]) == 9.0

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 10.0  # T1 finished, back to T2

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # T2 resumes
    assert schedule.running_inst is not None
    assert schedule.running_inst is task_2_inst_3  # ensure same object as before
    assert schedule.running_inst.task is task_2

    assert len(task_2_inst_3.preempts) == 1
    assert approx(task_2_inst_3.preempts[0]) == 9.0
    assert len(task_2_inst_3.resumes) == 1
    assert approx(task_2_inst_3.resumes[0]) == 10.0

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 11.0  # T2 done

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 0  # no tasks refreshed
    assert schedule.running_inst is None

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 12.0  # finished hyperperiod


def test_single_float_schedule_manual():
    task_1 = Task(1.5, 3.5, 2.5)
    workload = Workload([task_1])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 1.5

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 0
    assert schedule.running_inst is None

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 3.5

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 5.0


def test_multi_float_schedule_manual():
    task_1 = Task(1.5, 2, 2)
    task_2 = Task(1.0, 4, 10)  # large so task 1 is prioritized
    workload = Workload([task_1, task_2])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 1.5

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2
    task_2_inst_1 = schedule.running_inst

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 2.0  # T1 preempts T2

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    assert len(task_2_inst_1.preempts) == 1
    assert approx(task_2_inst_1.preempts[0]) == 2.0

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 3.5

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2

    assert len(task_2_inst_1.preempts) == 1
    assert approx(task_2_inst_1.preempts[0]) == 2
    assert len(task_2_inst_1.resumes) == 1
    assert approx(task_2_inst_1.resumes[0]) == 3.5

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 4.0
