import httpx


class CFError(Exception):
    """Something went wrong trying to communicate with CF"""


API = "https://codeforces.com/api/"


async def get_rating(handle: str) -> int | None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(API + "user.rating", params={"handle": handle})
            data = response.json()
        except httpx.TimeoutException as e:
            raise CFError("Codeforces API timed out") from e
        except httpx.HTTPError as e:
            raise CFError(f"Cannot connect to Codeforces: {e}") from e
        except ValueError as e:
            raise CFError("Codeforces didn't return JSON") from e

        if data.get("status") != "OK":
            raise CFError(data.get("comment", "Codeforces API denied the request"))

        history = data["result"]
        if not history:
            return None
        return history[-1]["newRating"]
