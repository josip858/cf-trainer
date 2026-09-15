import schemas


def get_picks(problemset: list[schemas.Problem], offsets: dict[int, int], user_rating: int | None,
              solved_problems: set[str] | None = None) -> schemas.PicksResponse:
    problemset = sorted(problemset, key=lambda problem: problem.solved_count, reverse=True)
    offsets = offsets.copy()

    assumed = False
    if user_rating is None:
        user_rating = 800
        assumed = True

    if solved_problems is None:
        solved_problems = set()

    response = []
    current_pick_count = 0
    total_pick_count = 0
    for count in offsets.values():
        total_pick_count += count

    for problem in problemset:
        dif = problem.rating - user_rating
        if offsets.get(dif, 0) > 0 and problem.id not in solved_problems:
            response.append(schemas.Pick(problem=problem, offset=dif))
            offsets[dif] -= 1
            current_pick_count += 1
        if total_pick_count == current_pick_count: break

    response.sort(key=lambda pick: pick.offset)
    return schemas.PicksResponse(picks=response, rating_source="assumed" if assumed else "cf")
