from fastapi import FastAPI
import picker,cf_client,schemas
import asyncio,time


app=FastAPI()

@app.get("/")
async def root()->dict:
    return {"message":"Hello World!"}

@app.get("/api/picks")
async def get_picks(handle:str)->schemas.PicksResponse:
    problemset = await cf_client.get_problemset()
    user_rating = await cf_client.get_user_rating(handle)
    solved_problems = await cf_client.get_solved_list(handle)
    return picker.get_picks(problemset, {100:2,300:1}, user_rating,solved_problems)