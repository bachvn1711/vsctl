from typing import Optional

from pydantic import BaseModel, Field


class Signal(BaseModel):
    parent: str
    name: str
    datatype: str

    description: str = ""

    unit: Optional[str] = None

    writable: bool = False

    minimum: Optional[float] = None

    maximum: Optional[float] = None


class Catalog(BaseModel):
    version: str = "0.1"

    signals: list[Signal] = Field(default_factory=list)