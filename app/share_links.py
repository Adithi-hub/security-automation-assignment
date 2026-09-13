import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user, get_password_hash, verify_password
from app.database import get_db


router = APIRouter(tags=["share links"])


class ShareCreate(BaseModel):
    password: Optional[str] = None


def generate_share_token() -> str:
    return secrets.token_urlsafe(32)


def get_expiry() -> datetime:
    return datetime.utcnow() + timedelta(hours=24)


def hash_share_password(password: str) -> str:
    return get_password_hash(password)


def check_share_password(password: str, password_hash: str) -> bool:
    return verify_password(password, password_hash)


@router.post("/scans/{scan_id}/share")
def create_share_link(
    scan_id: int,
    payload: ShareCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    scan = (
        db.query(models.ScanResult)
        .filter(
            models.ScanResult.id == scan_id,
            models.ScanResult.owner_id == current_user.id,
        )
        .first()
    )

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    token = generate_share_token()

    password_hash = None
    if payload.password:
        password_hash = hash_share_password(payload.password)

    share_link = models.ShareLink(
        token=token,
        scan_id=scan.id,
        expires_at=get_expiry(),
        password_hash=password_hash,
    )

    db.add(share_link)
    db.commit()
    db.refresh(share_link)

    return {
        "share_url": f"http://localhost:8000/share/{token}"
    }


@router.get("/share/{token}")
def get_shared_scan(
    token: str,
    password: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    share_link = (
        db.query(models.ShareLink)
        .filter(models.ShareLink.token == token)
        .first()
    )

    if not share_link:
        raise HTTPException(
            status_code=404,
            detail="Share link not found",
        )

    now = datetime.utcnow()

    if share_link.expires_at <= now:
        raise HTTPException(
            status_code=410,
            detail="Share link has expired",
        )

    if share_link.password_hash:
        if share_link.locked_until and share_link.locked_until > now:
            raise HTTPException(
                status_code=429,
                detail="Too many failed password attempts. Try again later.",
            )

        if not password:
            raise HTTPException(
                status_code=401,
                detail="Password required",
            )

        if not check_share_password(
            password,
            share_link.password_hash,
        ):
            share_link.failed_attempts += 1

            if share_link.failed_attempts >= 5:
                share_link.locked_until = now + timedelta(minutes=15)
                db.commit()

                raise HTTPException(
                    status_code=429,
                    detail="Too many failed password attempts. Try again later.",
                )

            db.commit()

            raise HTTPException(
                status_code=403,
                detail="Invalid password",
            )

        share_link.failed_attempts = 0
        share_link.locked_until = None
        db.commit()

    return share_link.scan