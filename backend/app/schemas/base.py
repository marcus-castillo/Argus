"""Shared schema configuration."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema that reads attributes off ORM instances."""

    model_config = ConfigDict(from_attributes=True)
