"""Embedding model wrapper — OpenAI text-embedding-3-small."""

from config import get_settings


class EmbeddingClient:
    """Wraps OpenAI embeddings with batching support.

    Model: text-embedding-3-small (1536 dimensions)
    Max batch size: 100 texts per API call.
    The AsyncOpenAI client is created lazily on first use.
    """

    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    MAX_BATCH = 100

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Return the AsyncOpenAI client, creating it on first call."""
        if self._client is None:
            from openai import AsyncOpenAI
            settings = get_settings()
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._client

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string. Returns 1536-dim vector."""
        response = await self._get_client().embeddings.create(
            model=self.MODEL,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in batches of 100.

        Returns list of vectors in the same order as input texts.
        """
        all_embeddings = []
        for i in range(0, len(texts), self.MAX_BATCH):
            batch = texts[i : i + self.MAX_BATCH]
            response = await self._get_client().embeddings.create(
                model=self.MODEL,
                input=batch,
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])
        return all_embeddings


# Singleton — OpenAI client created lazily on first call
embeddings = EmbeddingClient()
