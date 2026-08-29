import pytest, httpx, cf_client

handle = "tourist"
invalidHandle = "ajigjgioagiogfnmadgmj"


@pytest.mark.slow
async def test_get_rating_valid_handle() -> None:
    rating = await cf_client.get_rating(handle)
    assert isinstance(rating, int)


@pytest.mark.parametrize("error, regex", [(httpx.ConnectTimeout("monkeypatch - timed out"), "timed out"),
                                          (httpx.HTTPError("monkeypatch - Cannot connect"), "Cannot connect")])
async def test_get_rating_network_error(monkeypatch, error, regex) -> None:
    async def fake_get(self, *args, **kwargs):
        raise error

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    with pytest.raises(cf_client.CFError, match=regex):
        await cf_client.get_rating(handle)


async def test_get_rating_not_json(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, text="<html>")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    with pytest.raises(cf_client.CFError, match="didn't return JSON"):
        await cf_client.get_rating(handle)


@pytest.mark.slow
async def test_get_rating_invalid_handle() -> None:
    with pytest.raises(cf_client.CFError, match="not found"):
        await cf_client.get_rating(invalidHandle)


async def test_get_rating_no_contest(monkeypatch) -> None:
    async def fake_get(self, *args, **kwargs):
        return httpx.Response(200, json={"status": "OK", "result": []})

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    assert await cf_client.get_rating(handle) is None
