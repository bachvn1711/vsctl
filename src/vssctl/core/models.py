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
    def normalize_parent_path_spelling(cls, v: str) -> str:
        if isinstance(v, str):
            parts = v.split(".")
            normalized = []
            
            # Singular standard mapping
            singulars = {
                "wheels": "Wheel",
                "wheel": "Wheel",
                "doors": "Door",
                "door": "Door",
                "seats": "Seat",
                "seat": "Seat",
                "windows": "Window",
                "window": "Window",
                "wipers": "Wiper",
                "wiper": "Wiper",
            }
            
            # Plural standard mapping
            plurals = {
                "mirror": "Mirrors",
                "mirrors": "Mirrors",
                "interiorlight": "InteriorLights",
                "interiorlights": "InteriorLights",
                "exteriormirror": "ExteriorMirrors",
                "exteriormirrors": "ExteriorMirrors",
                "signalinglight": "SignalingLights",
                "signalinglights": "SignalingLights",
                "brakelight": "BrakeLights",
                "brakelights": "BrakeLights",
                "staticlight": "StaticLights",
                "staticlights": "StaticLights",
            }
            
            for part in parts:
                l_part = part.lower()
                if l_part in singulars:
                    normalized.append(singulars[l_part])
                elif l_part in plurals:
                    normalized.append(plurals[l_part])
                else:
                    normalized.append(part)
            return ".".join(normalized)
        return v


class Catalog(BaseModel):
    version: str = "0.1"

    signals: list[Signal] = Field(default_factory=list)