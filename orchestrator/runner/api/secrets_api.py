from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from runner.api.deps import require_operator_api_key
from runner.config import get_settings
from runner.db import get_db
from runner.models_extended import AppSecret
from runner.schemas import SecretMetaOut, SecretSet
from runner.security.crypto import encrypt_secret, get_fernet

router = APIRouter(prefix="/secrets", tags=["secrets"])
Db = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[SecretMetaOut], dependencies=[Depends(require_operator_api_key)])
def list_secret_names(db: Db) -> list[SecretMetaOut]:
    rows = db.execute(select(AppSecret)).scalars().all()
    return [
        SecretMetaOut(name=r.name, has_value=bool(r.ciphertext), updated_at=r.updated_at)
        for r in rows
    ]


@router.post("", status_code=204, dependencies=[Depends(require_operator_api_key)])
def set_secret(body: SecretSet, db: Db) -> None:
    fernet = get_fernet(get_settings().encryption_key)
    if fernet is None:
        raise HTTPException(status_code=503, detail="ENCRYPTION_KEY not configured")
    row = db.get(AppSecret, body.name)
    ct = encrypt_secret(fernet, body.value)
    if row:
        row.ciphertext = ct
    else:
        db.add(AppSecret(name=body.name, ciphertext=ct))
    db.commit()
