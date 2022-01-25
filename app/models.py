"""Pydantic models."""
from pydantic import BaseModel

class Services(BaseModel):
    """Services info."""
    __root__: dict[str, list[dict]]

class Operations(BaseModel):
    """Operations List."""
    __root__: dict[str, dict]
