import pytest

from scheduler import Task, Workload, count_task_preemptions, dm_schedule

factors = [
    1.0,
    0.1,
    0.01,
    0.001,
]


@pytest.mark.parametrize("factor", factors)
def test_workload_1(factor: float):
    workload = Workload(
        [
            Task(exec_time=3, period=10, rel_deadline=6),
            Task(5, 6, 7),
        ]
    )
    workload.set_factor(factor)
    schedule = dm_schedule(workload)
    assert schedule is None


@pytest.mark.parametrize("factor", factors)
def test_workload_2(factor: float):
    workload = Workload(
        [
            Task(5, 6, 7),
            Task(3, 10, 12),
        ]
    )
    workload.set_factor(factor)
    schedule = dm_schedule(workload)
    assert schedule is None


@pytest.mark.parametrize("factor", factors)
def test_workload_3(factor: float):
    workload = Workload(
        [
            Task(3, 10, 12),
            Task(4, 6, 8),
        ]
    )
    workload.set_factor(factor)
    schedule = dm_schedule(workload)
    assert schedule is not None

    preempts = count_task_preemptions(workload, schedule)
    assert preempts[0] == 3
    assert preempts[1] == 0


@pytest.mark.parametrize("factor", factors)
def test_workload_4(factor: float):
    workload = Workload(
        [
            Task(2, 10, 12),
            Task(8, 20, 7),
            Task(6, 15, 20),
            Task(5, 20, 15),
        ]
    )
    workload.set_factor(factor)
    schedule = dm_schedule(workload)
    assert schedule is None


@pytest.mark.parametrize("factor", factors)
def test_workload_5(factor: float):
    workload = Workload(
        [
            Task(2, 8, 16),
            Task(4, 20, 30),
            Task(5, 20, 25),
            Task(5, 25, 25),
        ]
    )
    workload.set_factor(factor)
    schedule = dm_schedule(workload)
    assert schedule is not None

    preempts = count_task_preemptions(workload, schedule)
    assert preempts[0] == 0
    assert preempts[1] == 8
    assert preempts[2] == 6
    assert preempts[3] == 4
