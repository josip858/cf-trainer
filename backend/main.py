from fastapi import FastAPI, HTTPException
import picker,cf_client,schemas

app=FastAPI()

@app.get("/")
async def root()->dict:
    return {"message":"Hello World!"}

@app.get("/api/picks")
async def get_picks(handle:str)->schemas.PicksResponse:
    handle=handle.strip()
    handle_size=len(handle)
    if handle_size<3 or handle_size>24:
        raise HTTPException(status_code=400,detail="Handle should contain between 3 and 24 characters, inclusive")
    try:
        user_rating = await cf_client.get_user_rating(handle)
        problemset = await cf_client.get_problemset()
        solved_problems = await cf_client.get_solved_list(handle)
        return picker.get_picks(problemset, {100:2,300:1}, user_rating,solved_problems)
    except cf_client.CFUserNotFound as e:
        raise HTTPException(status_code=404,detail=str(e))
    except cf_client.CFError as e:
        raise HTTPException(status_code=503,detail=str(e))