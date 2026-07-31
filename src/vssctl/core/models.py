from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Signal(BaseModel):
    parent: str
    name: str
    datatype: Optional[str] = None

    description: str = ""

    unit: Optional[str] = None

    writable: bool = False

    minimum: Optional[float] = None

    maximum: Optional[float] = None

    @field_validator("parent", mode="before")
    @classmethod
    def normalize_parent_wheels(cls, v: str) -> str:
        if isinstance(v, str):
            parts = v.split(".")
            normalized = []
            for part in parts:
                if part.lower() == "wheels":
                    normalized.append("Wheel")
                else:
                    normalized.append(part)
            return ".".join(normalized)
        return v


class Catalog(BaseModel):
    version: str = "0.1"

    signals: list[Signal] = Field(default_factory=list)