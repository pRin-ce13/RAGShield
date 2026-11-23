"""Pydantic Request and Response Schemas for Target RAG Applications."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TargetBase(BaseModel):
    """Shared target attributes."""
    name: str = Field(..., min_length=2, max_length=255, description="Target application identifier")
    target_url: str = Field(..., description="HTTP REST API base URL for querying the RAG system")
    description: Optional[str] = Field(None, description="Technical description of the RAG target")
    api_key: Optional[str] = Field(None, description="Authentication bearer token or API key for the target")
    custom_headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom HTTP headers")
    request_mapping: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Payload structure template")
    response_mapping: Optional[Dict[str, str]] = Field(default_factory=dict, description="Field mapping for answer & citations")


class TargetCreate(TargetBase):
    """Payload for registering a new Target."""
    pass


class TargetUpdate(BaseModel):
    """Payload for modifying an existing Target."""
    name: Optional[str] = None
    target_url: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    request_mapping: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None


class TargetResponse(BaseModel):
    """Public target response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    target_url: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TargetHealthResponse(BaseModel):
    """Pre-flight target connectivity verification result."""
    target_id: str
    target_name: str
    target_url: str
    is_reachable: bool
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    message: str
