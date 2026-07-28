from .storage import Storage
from .models import Signal


class CatalogService:

    def __init__(self):

        self.storage = Storage()

        self.catalog = self.storage.load()

    def list(self):

        return self.catalog.signals

    def add(self, signal: Signal):

        self.catalog.signals.append(signal)

        self.storage.save(self.catalog)

    def remove(self, parent: str, name: str):

        self.catalog.signals = [

            s

            for s in self.catalog.signals

            if not (s.parent == parent and s.name == name)

        ]

        self.storage.save(self.catalog)

    def search(self, keyword):

        keyword = keyword.lower()

        return [

            s

            for s in self.catalog.signals

            if keyword in s.name.lower()

        ]