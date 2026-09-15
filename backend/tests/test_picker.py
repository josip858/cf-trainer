import pytest, picker, schemas


def make_problem(contest_id: int | str,
                 index: str,
                 *,
                 name: str = "problem_name",
                 rating: int = 800,
                 tags: list[str] | None = None,
                 solved_count: int = 777) -> schemas.Problem:
    return schemas.Problem(contest_id=str(contest_id),
                           index=index,
                           name=name,
                           rating=rating,
                           tags=tags if tags is not None else [],
                           solved_count=solved_count)


@pytest.fixture
def problemset() -> list[schemas.Problem]:
    return [make_problem(1500, "A", rating=1100, solved_count=200),
            make_problem(1501, "A", rating=1300, solved_count=400),
            make_problem(1502, "A", rating=1100, solved_count=300),
            make_problem(1503, "A", rating=1100, solved_count=250),
            make_problem(1504, "A", rating=800, solved_count=200),
            make_problem(1505, "A", rating=900, solved_count=67)
            ]


def test_picker_get_picks(problemset):
    response = picker.get_picks(problemset, {100: 2, 300: 1}, 1000, {"1502A"})

    assert len(response.picks) == 3
    assert [pick.offset for pick in response.picks] == [100, 100, 300]
    assert [pick.problem.id for pick in response.picks] == ["1503A", "1500A", "1501A"]
    assert response.rating_source == "cf"


def test_picker_get_picks_no_user_rating(problemset):
    response = picker.get_picks(problemset, {100: 2, 300: 1},None)

    assert len(response.picks) == 2
    assert [pick.offset for pick in response.picks] == [100,300]
    assert [pick.problem.id for pick in response.picks] == ["1505A","1502A"]
    assert response.rating_source == "assumed"
