"""The HTTP API. One FastAPI app, two runtimes.

Locally it runs under uvicorn against the in-memory store, with the pipeline
executing as a background task. In AWS the same app runs inside a Lambda behind
API Gateway (see lambda_handler.py), against DynamoDB + S3, and POST /jobs hands
the work to SQS instead. Which one is in play is decided entirely by environment
variables — there is no second implementation to keep in sync.

One deliberate divergence from the §6 contract remains: POST /jobs takes the
transcript text directly instead of an S3 key, because the presigned-upload flow
(§3.1b) does not exist yet.

Local usage:
    uv run uvicorn services.api.app:app --reload --port 3001
"""

import logging
import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from services.pipeline.models import ApiModel, BacklogResult, Job

from . import export as export_module
from . import queue
from .auth import require_user_id
from .handlers import artifacts as artifact_handlers
from .handlers import jobs as job_handlers
from .job_store import Artifact
from .pipeline_runner import execute_job

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env.local")

logging.basicConfig(level=logging.INFO, format="%(message)s")

app = FastAPI(title="Agente PO — API")


def _allowed_origins() -> list[str]:
    """Locally this is the Next.js dev server; in AWS it is the CloudFront domain,
    injected by CDK. Never "*" — these requests carry a Clerk session token."""
    raw = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_route() -> dict[str, str]:
    """Unauthenticated liveness check — the one route with no Clerk dependency."""
    return {"status": "ok"}


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
    if not queue.enqueue_job(job.job_id, user_id, body.meeting_id):
        background_tasks.add_task(
            execute_job, job.job_id, user_id, body.meeting_id, body.transcript_text
        )
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
