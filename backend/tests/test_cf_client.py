import pytest, httpx, cf_client

HANDLE = "tourist"
INVALID_HANDLE = "ajigjgioagiogfnmadgmj"


@pytest.mark.slow
async def test_get_user_rating_valid() -> None:
    rating = await cf_client.get_user_rating(HANDLE)
    assert isinstance(rating, int)


async def test_get_user_rating_no_contest(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    assert await cf_client.get_user_rating(HANDLE) is None


@pytest.mark.slow
async def test_get_solved_list_valid() -> None:
    solved_list = await cf_client.get_solved_list(HANDLE)
    assert solved_list
    assert "2A" in solved_list


async def test_get_solved_list_no_submissions(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert await cf_client.get_solved_list(HANDLE) == set()


async def test_get_solved_list_no_wa(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": [
            {"verdict": "OK", "problem": {"contestId": 4, "index": "A"}},
            {"verdict": "WRONG_ANSWER", "problem": {"contestId": 71, "index": "A"}},
        ]})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert await cf_client.get_solved_list(HANDLE) == {"4A"}


@pytest.mark.slow
async def test_get_problemset() -> None:
    problemset = await cf_client.get_problemset()
    assert len(problemset) > 5000


async def test_get_problemset_problem_filter(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": {
            "problems": [
                {"name": "no_contest_id", "type": "PROGRAMMING",
                 "rating": 800, "tags": ["brute force", "math"]},
                {"contestId": 9999, "index": "A", "name": "unrated", "type": "PROGRAMMING",
                 "tags": []},
                {"contestId": 9998, "index": "A", "name": "valid1", "type": "PROGRAMMING",
                 "rating": 900, "tags": ["dp"]},
                {"contestId": 9997, "index": "B", "name": "valid2", "type": "PROGRAMMING",
                 "rating": 1200, "tags": ["math", "greedy"]},
            ],
            "problemStatistics": [
                {"contestId": 9997, "index": "B", "solvedCount": 42},
                {"contestId": 9998, "index": "A", "solvedCount": 777},
                { "index": "A", "solvedCount": 3},
                {"contestId": 4, "index": "A", "solvedCount": 500},
            ]}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    problems = await cf_client.get_problemset()

    # filter: leave unrated and no contest_id
    assert len(problems) == 2

    # mapping: every CF key is correctly mapped
    first = problems[0]
    assert first.id == "9998A"
    assert first.name == "valid1"
    assert first.rating == 900
    assert first.tags == ["dp"]
    assert first.url == "https://codeforces.com/problemset/problem/9998/A"

    # join: solved_count comes from corresponding problem, not from position
    assert first.solved_count == 777
    assert problems[1].solved_count == 42


@pytest.mark.parametrize("function", [cf_client.get_user_rating, cf_client.get_solved_list])
@pytest.mark.parametrize("error, regex", [(httpx.ConnectTimeout("monkeypatch - timed out"), "timed out"),
                                          (httpx.HTTPError("monkeypatch - Cannot connect"), "Cannot connect")])
async def test_network_error(monkeypatch, function, error, regex) -> None:
    async def fake_get(self, *args, **kwargs):
        raise error

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    with pytest.raises(cf_client.CFError, match=regex):
        await function(HANDLE)


@pytest.mark.parametrize("function", [cf_client.get_user_rating, cf_client.get_solved_list])
async def test_not_json(monkeypatch, function) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, text="<html>")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(cf_client.CFError, match="didn't return JSON"):
        await function(HANDLE)


@pytest.mark.slow
@pytest.mark.parametrize("function", [cf_client.get_user_rating, cf_client.get_solved_list])
async def test_invalid_handle(function) -> None:
    with pytest.raises(cf_client.CFError, match="not found"):
        await function(INVALID_HANDLE)
