from .storage import Storage
from .models import Signal
from .validator import Validator

class CatalogService:

    def __init__(self):

        self.storage = Storage()

        self.catalog = self.storage.load()

        self.validator = Validator()


    def list(self):

        return self.catalog.signals

    def add(self, signal: Signal):

        self.validator.validate(
                    signal,
                    self.catalog,
                )

        self.catalog.signals.append(signal)

        self.storage.save(self.catalog)

    def remove(self, parent: str, name: str):
        # Normalize the parent parameter to support full VSS singular/plural matching
        parent_norm = parent
        if parent:
            parts = parent.split(".")
            normalized = []
            singulars = {
                "wheels": "Wheel", "wheel": "Wheel",
                "doors": "Door", "door": "Door",
                "seats": "Seat", "seat": "Seat",
                "windows": "Window", "window": "Window",
                "wipers": "Wiper", "wiper": "Wiper",
                "mirrors": "Mirror", "mirror": "Mirror",
            }
            plurals = {
                "interiorlight": "InteriorLights", "interiorlights": "InteriorLights",
                "exteriormirror": "ExteriorMirrors", "exteriormirrors": "ExteriorMirrors",
                "signalinglight": "SignalingLights", "signalinglights": "SignalingLights",
                "brakelight": "BrakeLights", "brakelights": "BrakeLights",
                "staticlight": "StaticLights", "staticlights": "StaticLights",
            }
            for part in parts:
                l_part = part.lower()
                if l_part in singulars:
                    normalized.append(singulars[l_part])
                elif l_part in plurals:
                    normalized.append(plurals[l_part])
                else:
                    normalized.append(part)
            parent_norm = ".".join(normalized)

        self.catalog.signals = [

            s

            for s in self.catalog.signals

            if not (s.parent == parent_norm and s.name == name)

        ]

        self.storage.save(self.catalog)

    def search(self, keyword):

        keyword = keyword.lower()

        return [

            s

            for s in self.catalog.signals

            if keyword in s.name.lower()

        ]