"""Local-only dev server: exposes the pipeline over HTTP so it can be tested from
Postman or the frontend before any AWS infrastructure exists. NOT the production
API — that's API Gateway + Lambda (CLAUDE.md §11 step 4-5), built as thin handlers
around the exact same functions this server calls (handlers/, pipeline_runner.py,
job_store.py). POST /jobs here takes the transcript text directly instead of an S3
key, since there's no upload flow yet; that's the one deliberate divergence from
the real §6 contract.

Usage:
    uv run uvicorn services.api.local_server:app --reload --port 3001
"""

import logging
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from services.pipeline.models import ApiModel, BacklogResult, Job

from . import export as export_module
from .auth import require_user_id
from .handlers import artifacts as artifact_handlers
from .handlers import jobs as job_handlers
from .job_store import Artifact
from .pipeline_runner import execute_job

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env.local")

logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="Agente PO — local dev API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateJobRequest(ApiModel):
    meeting_id: str
    transcript_text: str


@app.post("/jobs", status_code=202)
async def create_job_route(
    body: CreateJobRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_user_id),
) -> Job:
    job = job_handlers.create_job(user_id, body.meeting_id, body.transcript_text)
    background_tasks.add_task(execute_job, job.job_id, body.meeting_id, body.transcript_text)
    return job


@app.get("/jobs")
async def list_jobs_route(user_id: str = Depends(require_user_id)) -> list[Job]:
    return job_handlers.list_jobs(user_id)


@app.get("/jobs/{job_id}")
async def get_job_route(job_id: str, user_id: str = Depends(require_user_id)) -> Job:
    job = job_handlers.get_job(user_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/jobs/{job_id}/result")
async def get_job_result_route(
    job_id: str, user_id: str = Depends(require_user_id)
) -> BacklogResult:
    result = job_handlers.get_job_result(user_id, job_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Result not found (job may not be completed yet)"
        )
    return result


@app.get("/jobs/{job_id}/export", response_model=None)
async def export_job_route(
    job_id: str,
    format: Literal["json", "markdown", "csv"] = Query("json"),
    user_id: str = Depends(require_user_id),
) -> PlainTextResponse | JSONResponse:
    result = job_handlers.get_job_result(user_id, job_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Result not found (job may not be completed yet)"
        )

    if format == "markdown":
        return PlainTextResponse(export_module.to_markdown(result), media_type="text/markdown")
    if format == "csv":
        return PlainTextResponse(export_module.to_csv(result), media_type="text/csv")
    return JSONResponse(content=result.model_dump(by_alias=True, mode="json"))


@app.patch("/artifacts/{artifact_id}")
async def patch_artifact_route(
    artifact_id: str, updates: dict[str, Any], user_id: str = Depends(require_user_id)
) -> Artifact:
    updated = artifact_handlers.patch_artifact(user_id, artifact_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return updated
