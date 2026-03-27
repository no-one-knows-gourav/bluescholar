"""Qdrant vector store client and collection helpers."""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from uuid import uuid4
from config import get_settings


class VectorStore:
    """Thin wrapper around Qdrant for multi-tenant vector operations.

    The QdrantClient is created lazily on first use so that importing this
    module does not fail when QDRANT_URL / QDRANT_API_KEY are absent.
    """

    EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small

    def __init__(self):
        self._client: QdrantClient | None = None

    def _get_client(self) -> QdrantClient:
        """Return the Qdrant client, creating it on first call."""
        if self._client is None:
            settings = get_settings()
            self._client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
        return self._client

    def _collection_name(self, institution_slug: str, user_id: str | None, collection_type: str) -> str:
        """Build namespaced collection name: {slug}_{user_id}_{type} or {slug}_{type}."""
        if user_id:
            return f"{institution_slug}_{user_id}_{collection_type}"
        return f"{institution_slug}_{collection_type}"

    def _build_filter(self, filters: dict | None) -> Filter | None:
        """Build a Qdrant Filter from a simple key→value dict."""
        if not filters:
            return None
        return Filter(must=[
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items()
        ])

    async def ensure_collection(self, name: str) -> None:
        """Create collection if it doesn't exist."""
        client = self._get_client()
        existing = {c.name for c in client.get_collections().collections}
        if name not in existing:
            client.create_collection(
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
        self._get_client().upsert(
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
        self._get_client().upsert(collection_name=collection, points=structs)
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
        client = self._get_client()
        try:
            # qdrant-client >= 1.9: use query_points
            result = client.query_points(
                collection_name=collection,
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=self._build_filter(filters),
            )
            return result.points
        except AttributeError:
            # Fallback for older qdrant-client versions
            return client.search(
                collection_name=collection,
                query_vector=query,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=self._build_filter(filters),
            )

    async def scroll(
        self,
        collection: str,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list:
        """Scroll through all points in a collection (paginated)."""
        points, _ = self._get_client().scroll(
            collection_name=collection,
            limit=limit,
            scroll_filter=self._build_filter(filters),
        )
        return points


# Singleton — QdrantClient created lazily on first method call
qdrant = VectorStore()


