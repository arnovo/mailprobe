"""Webhook delivery with retries and DLQ."""
from __future__ import annotations

import json
from typing import Any

import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import compute_webhook_signature
from app.tasks.celery_app import celery_app

engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def get_sync_session() -> Session:
    return SessionLocal()


def dispatch_webhook_event(workspace_id: int, event: str, payload: dict[str, Any]) -> None:
    """Enqueue webhook deliveries for all hooks subscribed to event."""
    from app.models import Webhook
    db = get_sync_session()
    try:
        r = db.execute(select(Webhook).where(Webhook.workspace_id == workspace_id, Webhook.is_active.is_(True)))
        hooks = list(r.scalars().all())
        for wh in hooks:
            events = [e.strip() for e in (wh.events or "").split(",") if e.strip()]
            if event in events:
                send_webhook_delivery.delay(wh.id, event, payload)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=5)
def send_webhook_delivery(self, webhook_id: int, event: str, payload: dict):
    """Send one webhook with retries and backoff."""
    db = get_sync_session()
    try:
        from app.models import Webhook, WebhookDelivery
        r = db.execute(select(Webhook).where(Webhook.id == webhook_id))
        wh = r.scalars().one_or_none()
        if not wh or not wh.is_active:
            return
        body = json.dumps({"event": event, "data": payload}).encode()
        signature = compute_webhook_signature(body, wh.secret)
        headers = {"Content-Type": "application/json", "X-Webhook-Signature": signature}
        try:
            resp = requests.post(
                wh.url,
                data=body,
                headers=headers,
                timeout=settings.webhook_timeout_seconds,
            )
            success = 200 <= resp.status_code < 300
        except Exception as exc:
            success = False
            resp = None
            error_msg = str(exc)[:2000]
        else:
            error_msg = ""

        delivery = WebhookDelivery(
            webhook_id=wh.id,
            event=event,
            payload=body.decode(),
            status_code=resp.status_code if resp else None,
            response_body=resp.text[:2000] if resp else error_msg,
            success=success,
            retry_count=self.request.retries,
        )
        db.add(delivery)
        db.commit()

        if not success and self.request.retries < self.max_retries:
            raise self.retry(countdown=2 ** self.request.retries)
    finally:
        db.close()
