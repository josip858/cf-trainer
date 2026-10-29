import asyncio
import datetime
import time

import httpx
import schemas


class CFError(Exception):
    """Something went wrong trying to communicate with CF"""


API = "https://codeforces.com/api/"
fetch_lock = asyncio.Lock()
last_fetch: float | None = None


async def _call_api(endpoint: str, params: dict | None = None) -> dict:
    global last_fetch
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            async with fetch_lock:
                if last_fetch is not None:
                    fetch_elapsed: float = time.monotonic() - last_fetch
                    if fetch_elapsed < 2.1:
                        await asyncio.sleep(2.1 - fetch_elapsed)
                last_fetch = time.monotonic()
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
    return set(str(submission["problem"]["contestId"]) + submission["problem"]["index"] for submission in submissions if
               "verdict" in submission and "contestId" in submission["problem"] and submission["verdict"] == "OK")


fetch_problemset_lock = asyncio.Lock()
last_problemset_fetch: datetime.date | None = None
saved_problemset: list[schemas.Problem] | None = None


async def get_problemset() -> list[schemas.Problem]:
    global last_problemset_fetch, saved_problemset
    async with fetch_problemset_lock:
        if saved_problemset is not None and last_problemset_fetch==datetime.date.today():
            return saved_problemset
        data = await _call_api("problemset.problems")
        problemset = data["result"]

        solved_count_by_id = {}
        problems = []
        for problem in problemset["problemStatistics"]:
            if "contestId" not in problem:
                continue
            solved_count_by_id[(problem["contestId"], problem["index"])] = problem["solvedCount"]

        for problem in problemset["problems"]:
            if not all(k in problem for k in ["contestId", "rating"]):
                continue
            problems.append(schemas.Problem(contest_id=str(problem["contestId"]),
                                            index=problem["index"],
                                            name=problem["name"],
                                            rating=problem["rating"],
                                            tags=problem["tags"],
                                            solved_count=solved_count_by_id[
                                                (problem["contestId"], problem["index"])]))
        last_problemset_fetch = datetime.date.today()
        saved_problemset=problems
    return problems
