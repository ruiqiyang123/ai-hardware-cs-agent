import hashlib
import math
import re

from langchain_core.embeddings import Embeddings


class LocalHashEmbeddings(Embeddings):
    """轻量本地 embedding，方便无外部 embedding key 时跑通 demo。"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = self._tokens(text)

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = text.lower()
        words = re.findall(r"[a-z0-9_]+|[\u4e00-\u9fff]", normalized)
        bigrams = [normalized[index:index + 2] for index in range(max(len(normalized) - 1, 0))]
        return words + bigrams
