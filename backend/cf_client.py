import httpx


class CFError(Exception):
    """Something went wrong trying to communicate with CF"""


API = "https://codeforces.com/api/"


async def _call_api(endpoint: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(API + endpoint, params=params)
            data = response.json()
        except httpx.TimeoutException as e:
            raise CFError("Codeforces API timed out") from e
        except httpx.HTTPError as e:
            raise CFError(f"Cannot connect to Codeforces: {e}") from e
        except ValueError as e:
            raise CFError("Codeforces didn't return JSON") from e

        if data.get("status") != "OK":
            raise CFError(data.get("comment", "Codeforces API denied the request"))

        return data


async def get_user_rating(handle: str) -> int | None:
    data = await _call_api("user.rating", {"handle": handle})

    history = data["result"]
    if not history:
        return None
    return history[-1]["newRating"]


async def get_solved_list(handle: str) -> set[str]:
    data = await _call_api("user.status", {"handle": handle})

    submissions = data["result"]
    if not submissions:
        return set()
    return set(str(problem["problem"]["contestId"]) + problem["problem"]["index"] for problem in submissions if
               problem["verdict"] == "OK")
