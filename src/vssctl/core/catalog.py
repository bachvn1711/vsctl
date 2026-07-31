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
        # Normalize the parent parameter to support "Wheels" -> "Wheel" matching
        parent_norm = parent
        if parent:
            parts = parent.split(".")
            parent_norm = ".".join(["Wheel" if p.lower() == "wheels" else p for p in parts])

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