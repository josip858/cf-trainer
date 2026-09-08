import pytest, httpx, cf_client

handle = "tourist"
invalid_handle = "ajigjgioagiogfnmadgmj"


@pytest.mark.slow
async def test_get_user_rating_valid() -> None:
    rating = await cf_client.get_user_rating(handle)
    assert isinstance(rating, int)


async def test_get_user_rating_no_contest(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    assert await cf_client.get_user_rating(handle) is None


@pytest.mark.slow
async def test_get_solved_list_valid() -> None:
    solved_list = await cf_client.get_solved_list(handle)
    assert solved_list
    assert "2A" in solved_list


async def test_get_solved_list_no_submissions(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert await cf_client.get_solved_list(handle) == set()


async def test_get_solved_list_no_wa(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": [
            {"verdict": "OK", "problem": {"contestId": 4, "index": "A"}},
            {"verdict": "WRONG_ANSWER", "problem": {"contestId": 71, "index": "A"}},
        ]})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    assert await cf_client.get_solved_list(handle) == {"4A"}


@pytest.mark.parametrize("function", [cf_client.get_user_rating, cf_client.get_solved_list])
@pytest.mark.parametrize("error, regex", [(httpx.ConnectTimeout("monkeypatch - timed out"), "timed out"),
                                          (httpx.HTTPError("monkeypatch - Cannot connect"), "Cannot connect")])
async def test_network_error(monkeypatch, function, error, regex) -> None:
    async def fake_get(self, *args, **kwargs):
        raise error

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    with pytest.raises(cf_client.CFError, match=regex):
        await function(handle)


@pytest.mark.parametrize("function", [cf_client.get_user_rating, cf_client.get_solved_list])
async def test_not_json(monkeypatch, function) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, text="<html>")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(cf_client.CFError, match="didn't return JSON"):
        await function(handle)


@pytest.mark.slow
@pytest.mark.parametrize("function", [cf_client.get_user_rating, cf_client.get_solved_list])
async def test_invalid_handle(function) -> None:
    with pytest.raises(cf_client.CFError, match="not found"):
        await function(invalid_handle)
