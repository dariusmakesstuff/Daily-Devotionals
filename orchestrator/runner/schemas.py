import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OutputModeSchema(str, Enum):
    audio_only = "audio_only"
    video = "video"


class RunCreate(BaseModel):
    output_mode: OutputModeSchema = OutputModeSchema.audio_only
    idempotency_key: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=64)
    meta: dict | None = None


class RunStepOut(BaseModel):
    id: uuid.UUID
    ordinal: int
    stage_key: str
    title: str
    status: str
    skipped_reason: str | None
    error_message: str | None
    detail: dict | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    id: uuid.UUID
    status: str
    output_mode: str
    idempotency_key: str | None
    correlation_id: str | None = None
    error_message: str | None
    meta: dict | None
    created_at: datetime
    updated_at: datetime
    steps: list[RunStepOut] = []

    model_config = {"from_attributes": True}


class IntegrationOut(BaseModel):
    key: str
    enabled: bool
    health_ok: bool | None = None
    config: dict | None = None


class IntegrationPatch(BaseModel):
    enabled: bool


class SecretSet(BaseModel):
    name: str = Field(..., max_length=128)
    value: str = Field(..., max_length=16000)


class SecretMetaOut(BaseModel):
    name: str
    has_value: bool
    updated_at: datetime | None = None


class EngagementRunCreate(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=128)
    correlation_id: str | None = Field(default=None, max_length=64)
    meta: dict | None = None


class EngagementStepOut(BaseModel):
    id: uuid.UUID
    ordinal: int
    stage_key: str
    title: str
    status: str
    skipped_reason: str | None
    error_message: str | None
    detail: dict | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class EngagementRunOut(BaseModel):
    id: uuid.UUID
    status: str
    idempotency_key: str | None
    correlation_id: str | None
    error_message: str | None
    meta: dict | None
    created_at: datetime
    updated_at: datetime
    steps: list[EngagementStepOut] = []

    model_config = {"from_attributes": True}


class WebhookEventIn(BaseModel):
    event: str = Field(..., max_length=64)
    run_id: uuid.UUID | None = None
    payload: dict | None = None
