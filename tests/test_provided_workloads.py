import pytest
import rootutils

from scheduler import count_task_preemptions, dm_schedule, load_workload

_proj_root = rootutils.setup_root(search_from=__file__)


def test_workload_1():
    workload = load_workload(_proj_root / "extra_files/workload1.txt")
    schedule = dm_schedule(workload)
    assert schedule is not None

    preempts = count_task_preemptions(workload, schedule)
    assert preempts[0] == 0
    assert preempts[1] == 1


def test_workload_2():
    workload = load_workload(_proj_root / "extra_files/workload2.txt")
    schedule = dm_schedule(workload)
    assert schedule is None


def test_workload_3():
    workload = load_workload(_proj_root / "extra_files/workload3.txt")
    schedule = dm_schedule(workload)
    assert schedule is not None

    preempts = count_task_preemptions(workload, schedule)
    assert preempts[0] == 0
    assert preempts[1] == 0
    assert preempts[2] == 0
    assert preempts[3] == 7
    assert preempts[4] == 0


def test_workload_4():
    workload = load_workload(_proj_root / "extra_files/workload4.txt")
    schedule = dm_schedule(workload)
    assert schedule is not None

    preempts = count_task_preemptions(workload, schedule)
    assert preempts[0] == 0
    assert preempts[1] == 1
    assert preempts[2] == 0
    assert preempts[3] == 0


def test_workload_5():
    workload = load_workload(_proj_root / "extra_files/workload5.txt")
    schedule = dm_schedule(workload)
    assert schedule is not None

    preempts = count_task_preemptions(workload, schedule)
    assert preempts[0] == 0
    assert preempts[1] == 3
    assert preempts[2] == 0
    assert preempts[3] == 0


def test_workload_6():
    workload = load_workload(_proj_root / "extra_files/workload6.txt")
    schedule = dm_schedule(workload)
    assert schedule is None
