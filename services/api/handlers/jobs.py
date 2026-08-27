from services.pipeline.models import BacklogResult, Job

from .. import job_store


def create_job(user_id: str, meeting_id: str, transcript: str) -> Job:
    return job_store.create_job(user_id, meeting_id, transcript)


def list_jobs(user_id: str) -> list[Job]:
    return job_store.list_jobs(user_id)


def get_job(user_id: str, job_id: str) -> Job | None:
    return job_store.get_job(job_id, user_id)


def get_job_result(user_id: str, job_id: str) -> BacklogResult | None:
    return job_store.get_result(job_id, user_id)
