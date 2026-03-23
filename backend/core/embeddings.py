"""Embedding model wrapper — OpenAI text-embedding-3-small."""

from openai import AsyncOpenAI
from config import get_settings


class EmbeddingClient:
    """Wraps OpenAI embeddings with batching support.

    Model: text-embedding-3-small (1536 dimensions)
    Max batch size: 100 texts per API call.
    """

    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    MAX_BATCH = 100

    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string. Returns 1536-dim vector."""
        response = await self._client.embeddings.create(
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
            response = await self._client.embeddings.create(
                model=self.MODEL,
                input=batch,
            )
            # Sort by index to preserve order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])
        return all_embeddings


# Singleton
embeddings = EmbeddingClient()
