import pytest
import rootutils

from pathlib import Path

from scheduler import Task, Workload, load_workload, parse_workload_file

workload_1, expected_1 = """
1,3,3
2,4,5
""", Workload(
    [
        Task(1, 3, 3),
        Task(2, 4, 5),
    ]
)


workload_2, expected_2 = """
2,14,25
4,16,17
8,21,25
5,20,30
7,14,25

""", Workload(
    [
        Task(2, 14, 25),
        Task(4, 16, 17),
        Task(8, 21, 25),
        Task(5, 20, 30),
        Task(7, 14, 25),
    ]
)

workload_3, expected_3 = """
1,14,25
3,16,17
1,21,25
2,20,30
1,14,25

""", Workload(
    [
        Task(1, 14, 25),
        Task(3, 16, 17),
        Task(1, 21, 25),
        Task(2, 20, 30),
        Task(1, 14, 25),
    ]
)

workload_4, expected_4 = """
2,4,6
1.5,8,10
1.5,8,9
1,8,15
""", Workload(
    [
        Task(2, 4, 6),
        Task(1.5, 8, 10),
        Task(1.5, 8, 9),
        Task(1, 8, 15),
    ]
)

workload_5, expected_5 = """
1,4,2
3,6,10
1,8,9
1,12,12
""", Workload(
    [
        Task(1, 4, 2),
        Task(3, 6, 10),
        Task(1, 8, 9),
        Task(1, 12, 12),
    ]
)

workload_6, expected_6 = """
2,4,6
1.5,8,10
1.5,8,9
1,8,15
1.5,16,20
""", Workload(
    [
        Task(2, 4, 6),
        Task(1.5, 8, 10),
        Task(1.5, 8, 9),
        Task(1, 8, 15),
        Task(1.5, 16, 20),
    ]
)


@pytest.mark.parametrize(
    "workload,expected",
    [
        (workload_1, expected_1),
        (workload_2, expected_2),
        (workload_3, expected_3),
        (workload_4, expected_4),
        (workload_5, expected_5),
    ],
)
def test_parse_workload(workload: str, expected: Workload):
    parsed_workload = parse_workload_file(workload)
    assert parsed_workload == expected


_proj_root = rootutils.setup_root(search_from=__file__)


@pytest.mark.parametrize(
    "path,expected",
    [
        (_proj_root / "extra_files/workload1.txt", expected_1),
        (_proj_root / "extra_files/workload2.txt", expected_2),
        (_proj_root / "extra_files/workload3.txt", expected_3),
        (_proj_root / "extra_files/workload4.txt", expected_4),
        (_proj_root / "extra_files/workload5.txt", expected_5),
        (_proj_root / "extra_files/workload6.txt", expected_6),
    ],
)
def test_load_workload(path: Path, expected: Workload):
    workload = load_workload(path)
    assert workload == expected
