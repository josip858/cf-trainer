from typing import Literal

from pydantic import BaseModel, computed_field


class Problem(BaseModel):
    contest_id: str
    index: str
    name: str
    rating: int
    tags: list[str]
    solved_count: int

    @computed_field
    @property
    def url(self) -> str:
        return f"https://codeforces.com/problemset/problem/{self.contest_id}/{self.index}"

    @computed_field
    @property
    def id(self) -> str:
        return self.contest_id + self.index


class Pick(BaseModel):
    problem: Problem
    offset: int



class PicksResponse(BaseModel):
    picks: list[Pick]
    rating_source: Literal["cf", "assumed", "custom"]
