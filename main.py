from fastapi import FastAPI, Request, HTTPException
import redis
from time import time

app = FastAPI()

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Rate limit config
MAX_ATTEMPTS = 5
TIME_WINDOW = 60  # in seconds

def is_rate_limited(identifier: str) -> bool:
    """
    Returns True if user/IP exceeded rate limit, else False
    """
    key = f"rate_limit:{identifier}"
    current_time = int(time())

    # Start a pipeline for atomic Redis transactions
    pipeline = r.pipeline()

    # Remove entries older than TIME_WINDOW
    pipeline.zremrangebyscore(key, 0, current_time - TIME_WINDOW)
    # Add new login attempt with current timestamp
    pipeline.zadd(key, {str(current_time): current_time})
    # Get total attempts in the current window
    pipeline.zcard(key)
    # Set key expiry
    pipeline.expire(key, TIME_WINDOW)
    
    _, _, attempt_count, _ = pipeline.execute()
    

    return attempt_count > MAX_ATTEMPTS

@app.post("/login")
async def login(request: Request):
    ip = request.client.host

    if is_rate_limited(ip):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    # Simulate a successful login (replace with real logic)
    return {"message": "Login attempt recorded"}
