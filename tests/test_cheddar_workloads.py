import pytest

from scheduler import Task, Workload, dm_schedule

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
