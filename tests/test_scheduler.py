# type: ignore

from pytest import approx

from scheduler import (
    AdvancingSchedule,
    Task,
    Workload,
    dm_advance_exec,
    dm_make_scheduling_decision,
)


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


def test_precision_multi_float_schedule_manual():
    task_1 = Task(1.512, 1.876, 2)
    task_2 = Task(1.458, 4.076, 10)  # large so task 1 is prioritized
    workload = Workload([task_1, task_2])
    schedule = AdvancingSchedule()

    # runs task 1(1) given higher deadline priority
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # task 1(1), task 2(1)
    assert schedule.created_insts[0].task is task_1
    assert schedule.created_insts[1].task is task_2
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 1.512

    # task 1(1) terminates so now runs task 2(1) until preempted by new task 1(2)
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # task 2(1)
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 1.876

    # task 1(2) runs until termination
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # task 1(2), task 2(1)
    assert schedule.created_insts[2].task is task_1
    assert len(schedule.created_insts[1].preempts) == 1
    assert len(schedule.created_insts[1].resumes) == 0
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 1.512 + 1.876

    # task 1(2) terminates so now continues to run task 2(1) until preempted by new task 1(3)
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 1  # task 2(1)
    assert len(schedule.created_insts[1].preempts) == 1
    assert len(schedule.created_insts[1].resumes) == 1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 2 * 1.876

    # task 1(3) runs until a new task 2(2) instance is released (but no preemption)
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # task 1(3), task 2(1)
    assert schedule.created_insts[3].task is task_1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 4.076

    # task 1(3) continues to run with no preemption
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 3  # task 1(3), task 2(1), task 2(2)
    assert schedule.created_insts[4].task is task_2
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1
    assert schedule.running_inst is schedule.created_insts[3]  # most recent task 1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 2 * 1.876 + 1.512

    # task 2(1) continues to run until preempted by new task 1(4)
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # task 2(1), task 2(2)
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2
    assert schedule.running_inst is schedule.created_insts[1]  # still first task 2

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 3 * 1.876

    # task 1(4) runs until completion (as no task 2 instances are released)
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 3  # task 1(4), task 2(1), task 2(2)
    assert schedule.created_insts[5].task is task_1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1
    assert schedule.running_inst is schedule.created_insts[5]  # most recent task 1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 3 * 1.876 + 1.512

    # task 2(1) resumes and runs until preempted by new task 1(5)
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # task 2(1), task 2(2)
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2
    assert schedule.running_inst is schedule.created_insts[1]  # still first task 2

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 4 * 1.876

    # task 1(5) runs until a new task 2(3) is released (but no preemption)
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 3  # task 1(5), task 2(1), task 2(2)
    assert schedule.created_insts[5].task is task_1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1
    assert schedule.running_inst is schedule.created_insts[6]  # most recent task 1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 2 * 4.076

    # task 1(5) runs until completion
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 4  # task 1(5), task 2(1), task 2(2), task 2(3)
    assert schedule.created_insts[7].task is task_2
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1
    assert schedule.running_inst is schedule.created_insts[6]  # most recent task 1

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 4 * 1.876 + 1.512

    # task 2(1) finally able to fun to completion without preemption
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 3  # task 2(1), task 2(2), task 2(3)
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2
    assert schedule.running_inst is schedule.created_insts[1]  # still first task 2

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 4 * 1.876 + 1.512 + 0.002

    # task 2(2) is next highest priority task due to having an earlier release (while same rel. deadline) and
    # runs until preemption when task 1(6) is created
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2  # task 2(2), task 2(3)
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_2
    assert schedule.running_inst is schedule.created_insts[4]

    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 5 * 1.876

    # task 1(6) is released and begins execution
    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 3  # task 1(6), task 2(2), task 2(3)
    assert schedule.created_insts[8].task is task_1
    assert schedule.running_inst is not None
    assert schedule.running_inst.task is task_1
    assert schedule.running_inst is schedule.created_insts[8]

    # no further advancing of the simulation as this has tested for all decimal issues


def test_precision_triple_float_schedule_manual_order_1():
    task_1 = Task(0.123, 0.3, 2.0)
    task_2 = Task(0.234, 0.6, 3.0)
    task_3 = Task(0.345, 0.9, 4.0)
    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123  # end of t1

    print(schedule.created_insts[1].remaining_exec_time)

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    remaining_time = schedule.running_inst.remaining_exec_time
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123 + remaining_time

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_3
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.6


def test_precision_triple_float_schedule_manual_order_2():
    task_1 = Task(0.123, 0.3, 2.0)
    task_2 = Task(0.234, 0.6, 4.0)
    task_3 = Task(0.345, 0.9, 3.0)
    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_3
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123  # end of t1

    print(schedule.created_insts[1].remaining_exec_time)

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_3
    remaining_time = schedule.running_inst.remaining_exec_time
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123 + remaining_time

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.6


def test_precision_triple_float_schedule_manual_order_3():
    task_1 = Task(0.123, 0.3, 2.0)
    task_2 = Task(0.234, 0.6, 3.0)
    task_3 = Task(0.345, 0.9, 3.0)
    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123  # end of t1

    print(schedule.created_insts[1].remaining_exec_time)

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    remaining_time = schedule.running_inst.remaining_exec_time
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123 + remaining_time

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_3
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.6


def test_precision_triple_float_schedule_manual_order_3():
    task_1 = Task(0.123, 0.3, 2.0)
    task_2 = Task(0.234, 0.6, 3.0)
    task_3 = Task(0.345, 0.9, 3.0)
    workload = Workload([task_1, task_3, task_2])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_3
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123  # end of t1

    print(schedule.created_insts[1].remaining_exec_time)

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_3
    remaining_time = schedule.running_inst.remaining_exec_time
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123 + remaining_time

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.6


# test failing cases


def test_precision_triple_float_schedule_manual_fail_1():
    # test failure of the highest priority task

    task_1 = Task(0.123, 0.3, 0.12)
    task_2 = Task(0.234, 0.6, 3.0)
    task_3 = Task(0.345, 0.9, 4.0)
    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert not dm_make_scheduling_decision(workload, schedule)

    ##################################################################

    task_1 = Task(0.123, 0.3, 0.123)  # deadline is end of execution (still ok)
    task_2 = Task(0.234, 0.6, 3.0)
    task_3 = Task(0.345, 0.9, 4.0)
    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)


def test_precision_triple_float_schedule_manual_fail_2():
    task_1 = Task(0.123, 0.3, 0.123)  # ensure remains highest priority
    task_2 = Task(0.234, 0.6, 0.23)  # always fail due to preemption
    task_3 = Task(0.345, 0.9, 4.0)
    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert not dm_make_scheduling_decision(workload, schedule)

    ##################################################################

    task_1 = Task(0.123, 0.3, 0.123)  # ensure remains highest priority
    task_2 = Task(0.234, 0.6, 0.234)  # always fail due to preemption
    task_3 = Task(0.345, 0.9, 4.0)
    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert not dm_make_scheduling_decision(workload, schedule)

    ##################################################################

    task_1 = Task(0.123, 0.3, 0.123)  # ensure remains highest priority
    task_2 = Task(0.256, 0.6, 2 * 0.123 + 0.256 - 0.001)  # always fail due to preemption
    task_3 = Task(0.345, 0.9, 4.0)

    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    remaining_time = schedule.running_inst.remaining_exec_time
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123 + remaining_time  # end of t2

    assert not dm_make_scheduling_decision(workload, schedule)

    ##################################################################

    task_1 = Task(0.123, 0.3, 0.123)  # ensure remains highest priority
    task_2 = Task(0.256, 0.6, 2 * 0.123 + 0.256)  # doesn't fail due to matching the delay up exactly
    task_3 = Task(0.345, 0.9, 4.0)

    workload = Workload([task_1, task_2, task_3])
    schedule = AdvancingSchedule()

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3  # release of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_1
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123  # end of t1

    assert dm_make_scheduling_decision(workload, schedule)
    assert schedule.running_inst.task is task_2
    remaining_time = schedule.running_inst.remaining_exec_time
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.3 + 0.123 + remaining_time  # end of t2

    assert dm_make_scheduling_decision(workload, schedule)


def test_precision_same_period():
    task_1 = Task(0.123, 0.789, 0.789)
    task_2 = Task(0.666, 0.789, 0.789)
    workload = Workload([task_1, task_2])
    schedule = AdvancingSchedule()

    assert len(schedule.pending_insts) == 0

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.123

    assert dm_make_scheduling_decision(workload, schedule)
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.789

    assert len(schedule.created_insts) == 2
    assert len(schedule.pending_insts) == 1

    assert dm_make_scheduling_decision(workload, schedule)
    assert len(schedule.pending_insts) == 2
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.789 + 0.123

    assert dm_make_scheduling_decision(workload, schedule)
    dm_advance_exec(workload, schedule)
    assert approx(schedule.time) == 0.789 + 0.789

    assert len(schedule.created_insts) == 4
    assert len(schedule.pending_insts) == 1
