from app.storage.base import StorageBackend


class InMemoryStorageBackend(StorageBackend):
    def __init__(self) -> None:
        self._store: dict[str, tuple[bytes, str]] = {}

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._store[key] = (data, content_type)

    def get(self, key: str) -> bytes:
        if key not in self._store:
            raise KeyError(f"Object not found: {key}")
        return self._store[key][0]

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def head(self, key: str) -> dict:
        if key not in self._store:
            raise KeyError(f"Object not found: {key}")
        return {"ContentLength": len(self._store[key][0])}
