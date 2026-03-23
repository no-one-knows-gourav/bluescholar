"""Qdrant vector store client and collection helpers."""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)
from uuid import uuid4
from config import get_settings


class VectorStore:
    """Thin wrapper around Qdrant for multi-tenant vector operations."""

    EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small

    def __init__(self):
        settings = get_settings()
        self._client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )

    def _collection_name(self, institution_slug: str, user_id: str | None, collection_type: str) -> str:
        """Build namespaced collection name: {slug}_{user_id}_{type} or {slug}_{type}."""
        if user_id:
            return f"{institution_slug}_{user_id}_{collection_type}"
        return f"{institution_slug}_{collection_type}"

    async def ensure_collection(self, name: str) -> None:
        """Create collection if it doesn't exist."""
        collections = self._client.get_collections().collections
        existing = {c.name for c in collections}
        if name not in existing:
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=self.EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

    async def upsert(
        self,
        collection: str,
        vector: list[float],
        payload: dict,
        point_id: str | None = None,
    ) -> str:
        """Upsert a single point. Returns the point ID."""
        pid = point_id or str(uuid4())
        await self.ensure_collection(collection)
        self._client.upsert(
            collection_name=collection,
            points=[PointStruct(id=pid, vector=vector, payload=payload)],
        )
        return pid

    async def upsert_batch(
        self,
        collection: str,
        points: list[dict],  # each: {vector, payload, id?}
    ) -> int:
        """Batch upsert. Returns count of inserted points."""
        await self.ensure_collection(collection)
        structs = [
            PointStruct(
                id=p.get("id", str(uuid4())),
                vector=p["vector"],
                payload=p["payload"],
            )
            for p in points
        ]
        self._client.upsert(collection_name=collection, points=structs)
        return len(structs)

    async def search(
        self,
        collection: str,
        query: list[float],
        limit: int = 5,
        score_threshold: float = 0.0,
        filters: dict | None = None,
    ) -> list:
        """Semantic search. Returns list of ScoredPoint."""
        query_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            query_filter = Filter(must=conditions)

        return self._client.search(
            collection_name=collection,
            query_vector=query,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

    async def scroll(
        self,
        collection: str,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list:
        """Scroll through all points in a collection (paginated)."""
        query_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            query_filter = Filter(must=conditions)

        points, _ = self._client.scroll(
            collection_name=collection,
            limit=limit,
            scroll_filter=query_filter,
        )
        return points


# Singleton
qdrant = VectorStore()
