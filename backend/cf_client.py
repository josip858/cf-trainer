import httpx


class CFError(Exception):
    """Something went wrong trying to communicate with CF"""


API = "https://codeforces.com/api/"


async def _call_api(endpoint: str, params: dict | None = None) -> dict:
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


async def get_problemset() -> dict[str, dict]:
    data = await _call_api("problemset.problems")
    problemset = data["result"]

    solved_count_by_id = {}
    problems_by_id = {}
    for problem in problemset["problemStatistics"]:
        if "contestId" not in problem:
            continue
        solved_count_by_id[str(problem["contestId"]) + problem["index"]] = problem["solvedCount"]

    for problem in problemset["problems"]:
        if not all(k in problem for k in ["contestId", "rating"]):
            continue
        problem_id = str(problem["contestId"]) + problem["index"]
        problems_by_id[problem_id] = {
            "name": problem["name"],
            "rating": problem["rating"],
            "tags": problem["tags"],
            "solved_count": solved_count_by_id[problem_id]
        }

    return problems_by_id
