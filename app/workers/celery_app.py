"""Celery 异步任务：把耗时的拉取/解析/审查放到后台执行。

启动：celery -A app.workers.celery_app worker -l info
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "contract_review",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_track_started=True,
    result_expires=3600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="contract_review.pull")
def pull_task(limit: int = 20):
    from app.core.database import SessionLocal
    from app.services.fetch_service import pull_and_dedupe

    db = SessionLocal()
    try:
        return pull_and_dedupe(db, limit)
    finally:
        db.close()


@celery_app.task(name="contract_review.parse")
def parse_task(task_id: int, document_id: int | None = None):
    from app.core.database import SessionLocal
    from app.services.parse_service import run_parse

    db = SessionLocal()
    try:
        return run_parse(db, task_id, document_id)
    finally:
        db.close()


@celery_app.task(name="contract_review.review")
def review_task(task_id: int):
    from app.core.database import SessionLocal
    from app.services.rule_service import review_task as do_review

    db = SessionLocal()
    try:
        return do_review(db, task_id)
    finally:
        db.close()


@celery_app.task(name="contract_review.write_comment")
def write_comment_task(task_id: int, instance_id: str, review_id: int):
    from app.core.database import SessionLocal
    from app.services.comment_service import write

    db = SessionLocal()
    try:
        return write(db, task_id, instance_id, review_id)
    finally:
        db.close()
