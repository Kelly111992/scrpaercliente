from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
import uuid
import asyncio
import json
import os
import pandas as pd
from scraper import scraper_instance
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    max_leads: int = 50
    delay_min_ms: int = 1000
    delay_max_ms: int = 3000
    extract_website: bool = True
    extract_phone: bool = True

# Store progress events for SSE
job_events = {}

@app.post("/scrape/start")
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job_events[job_id] = asyncio.Queue()
    
    async def status_callback(event_data):
        await job_events[job_id].put(event_data)

    background_tasks.add_task(
        scraper_instance.scrape,
        job_id,
        request.url,
        request.max_leads,
        request.delay_min_ms,
        request.delay_max_ms,
        request.extract_website,
        request.extract_phone,
        status_callback
    )
    
    return {"job_id": job_id}

@app.get("/scrape/stream/{job_id}")
async def stream_scrape(job_id: str):
    if job_id not in job_events:
        return JSONResponse(status_code=404, content={"message": "Job not found"})

    async def event_generator():
        queue = job_events[job_id]
        while True:
            event = await queue.get()
            yield {
                "data": json.dumps(event)
            }
            if event["type"] in ["done", "error"]:
                break

    return EventSourceResponse(event_generator())

@app.get("/scrape/result/{job_id}")
async def get_result(job_id: str):
    if job_id not in scraper_instance.jobs:
        return JSONResponse(status_code=404, content={"message": "Job not found"})
    return scraper_instance.jobs[job_id]

@app.get("/scrape/result/{job_id}.csv")
async def get_csv(job_id: str):
    if job_id not in scraper_instance.jobs:
        return JSONResponse(status_code=404, content={"message": "Job not found"})
    
    leads = scraper_instance.jobs[job_id]["leads"]
    df = pd.DataFrame(leads)
    
    file_path = f"results_{job_id}.csv"
    df.to_csv(file_path, index=False)
    
    return FileResponse(file_path, media_type="text/csv", filename="leads.csv")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
