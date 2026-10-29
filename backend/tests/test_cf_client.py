import asyncio
import datetime
import time

import pytest, httpx, cf_client

import schemas
from cf_client import fetch_lock, fetch_problemset_lock, saved_problemset, last_problemset_fetch

HANDLE = "tourist"
INVALID_HANDLE = "ajigjgioagiogfnmadgmj"


@pytest.fixture(autouse=True)
def reset_cf_state(monkeypatch):
    monkeypatch.setattr(cf_client, "saved_problemset", None)
    monkeypatch.setattr(cf_client, "last_problemset_fetch", None)
    monkeypatch.setattr(cf_client, "last_fetch", None)
    monkeypatch.setattr(cf_client, "fetch_lock", asyncio.Lock())
    monkeypatch.setattr(cf_client, "fetch_problemset_lock", asyncio.Lock())


async def test__call_api_limiter(monkeypatch)-> None:
    sent_at=[]
    async def fake_get(self,*args,**kwargs):
        sent_at.append(time.monotonic())
        return httpx.Response(200,json={"status":"OK"})
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    await asyncio.gather(cf_client._call_api("problemset.problems"), cf_client._call_api("problemset.problems"))
    assert len(sent_at)==2
    assert sent_at[1]-sent_at[0]>=2.1

@pytest.mark.slow
async def test_get_user_rating_valid() -> None:
    rating = await cf_client.get_user_rating(HANDLE, )
    assert isinstance(rating, int)


async def test_get_user_rating_no_contest(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    assert await cf_client.get_user_rating(HANDLE, ) is None


@pytest.mark.slow
async def test_get_solved_list_valid() -> None:
    solved_list = await cf_client.get_solved_list(HANDLE, )
    assert solved_list
    assert "2A" in solved_list


async def test_get_solved_list_no_submissions(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert await cf_client.get_solved_list(HANDLE, ) == set()


async def test_get_solved_list_no_wa(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": [
            {"verdict": "OK", "problem": {"contestId": 4, "index": "A"}},
            {"verdict": "WRONG_ANSWER", "problem": {"contestId": 71, "index": "A"}},
        ]})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert await cf_client.get_solved_list(HANDLE, ) == {"4A"}


async def test_get_solved_list_missing_keys(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": [
            {"problem": {"contestId": 4, "index": "A"}},
            {"verdict": "OK", "problem": {"contestId": 5, "index": "A"}},
            {"verdict": "OK", "problem": {}}
        ]})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert await cf_client.get_solved_list(HANDLE, ) == {"5A"}


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
                {"index": "A", "solvedCount": 3},
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


async def test_get_problemset_cache_no_fetch(monkeypatch) -> None:
    monkeypatch.setattr(cf_client, "saved_problemset",
                        [schemas.Problem(contest_id='2276', index='G', name='Elimination of Players', rating=2100,
                                         tags=['combinatorics', 'dp', 'math'], solved_count=333),
                         schemas.Problem(contest_id='2276', index='F', name='Permutation Coloring Game', rating=2400,
                                         tags=['brute force', 'dp', 'dsu', 'games', 'greedy', 'implementation', 'math'],
                                         solved_count=739)])

    monkeypatch.setattr(cf_client, "last_problemset_fetch", datetime.date.today())

    async def fake_get(self, *args, **kwargs):
        pytest.fail("A valid problemset cache shouldn't fetch again")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    problems = await cf_client.get_problemset()
    assert len(problems) == 2
    assert problems[0].id == "2276G"
    assert problems[1].id == "2276F"
    assert len(cf_client.saved_problemset) == 2


async def test_get_problemset_caching(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": {
            "problems": [{"contestId": 9997, "index": "B", "name": "valid2", "type": "PROGRAMMING",
                          "rating": 1200, "tags": ["math", "greedy"]}], "problemStatistics": [
                {"contestId": 9997, "index": "B", "solvedCount": 42}]}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    problems = await cf_client.get_problemset()
    assert cf_client.last_problemset_fetch == datetime.date.today()
    assert problems[0].id == "9997B"
    assert cf_client.saved_problemset[0].id == "9997B"

async def test_get_problemset_last_fetch_yesterday(monkeypatch) -> None:
    monkeypatch.setattr(cf_client, "last_problemset_fetch",datetime.date.today()-datetime.timedelta(days=1))
    monkeypatch.setattr(cf_client, "saved_problemset",
                        [schemas.Problem(contest_id='2276', index='G', name='Elimination of Players', rating=2100,
                                         tags=['combinatorics', 'dp', 'math'], solved_count=333),
                         schemas.Problem(contest_id='2276', index='F', name='Permutation Coloring Game', rating=2400,
                                         tags=['brute force', 'dp', 'dsu', 'games', 'greedy', 'implementation', 'math'],
                                         solved_count=739)])

    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": {
            "problems": [{"contestId": 9997, "index": "B", "name": "valid2", "type": "PROGRAMMING",
                          "rating": 1200, "tags": ["math", "greedy"]}], "problemStatistics": [
                {"contestId": 9997, "index": "B", "solvedCount": 42}]}})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    await cf_client.get_problemset()
    assert cf_client.last_problemset_fetch == datetime.date.today()
    assert len(cf_client.saved_problemset)==1

async def test_get_problemset_fetch_failure_preserves_cache(monkeypatch) -> None:
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    old_problems = [
        schemas.Problem(
            contest_id="123",
            index="A",
            name="Old problem",
            rating=800,
            tags=[],
            solved_count=10,
        )
    ]

    monkeypatch.setattr(cf_client, "saved_problemset", old_problems)
    monkeypatch.setattr(cf_client, "last_problemset_fetch", yesterday)

    async def fake_call_api(endpoint, *args, **kwargs):
        raise cf_client.CFError("Simulated bug")

    monkeypatch.setattr(cf_client, "_call_api", fake_call_api)

    with pytest.raises(cf_client.CFError, match="Simulated bug"):
        await cf_client.get_problemset()

    assert cf_client.saved_problemset == old_problems
    assert cf_client.last_problemset_fetch == yesterday


async def test_get_problemset_lock(monkeypatch) -> None:
    call_count=0

    async def fake_get(endpoint, *args, **kwargs):
        nonlocal call_count
        await asyncio.sleep(0)
        call_count += 1
        return {"status": "OK", "result": {
            "problems": [{"contestId": 9997, "index": "B", "name": "valid2", "type": "PROGRAMMING",
                          "rating": 1200, "tags": ["math", "greedy"]}], "problemStatistics": [
                {"contestId": 9997, "index": "B", "solvedCount": 42}]}}

    monkeypatch.setattr(cf_client, "_call_api", fake_get)
    first_fetch,second_fetch =await asyncio.gather(cf_client.get_problemset(), cf_client.get_problemset())
    assert call_count == 1
    assert first_fetch == second_fetch


@pytest.mark.parametrize("function, args",
                         [(cf_client.get_user_rating, (HANDLE,)),
                          (cf_client.get_solved_list, (HANDLE,)),
                          (cf_client.get_problemset, ())])
@pytest.mark.parametrize("error, regex",
                         [(httpx.ConnectTimeout("monkeypatch - timed out"), "timed out"),
                          (httpx.HTTPError("monkeypatch - Cannot connect"), "Cannot connect")])
async def test_network_error(monkeypatch, function, args, error, regex) -> None:
    async def fake_get(self, *args, **kwargs):
        raise error

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    with pytest.raises(cf_client.CFError, match=regex):
        await function(*args)


@pytest.mark.parametrize("function, args",
                         [(cf_client.get_user_rating, (HANDLE,)), (cf_client.get_solved_list, (HANDLE,)),
                          (cf_client.get_problemset, ())])
async def test_not_json(monkeypatch, function, args) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, text="<html>")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(cf_client.CFError, match="didn't return JSON"):
        await function(*args)


@pytest.mark.slow
@pytest.mark.parametrize("function", [cf_client.get_user_rating, cf_client.get_solved_list])
async def test_invalid_handle(function) -> None:
    with pytest.raises(cf_client.CFError, match="not found"):
        await function(INVALID_HANDLE)
