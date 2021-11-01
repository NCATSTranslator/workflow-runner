"""Pydantic models."""
from pydantic import BaseModel, HttpUrl


class Services(BaseModel):
    """Services info."""
    __root__: dict[str, list[dict]]
