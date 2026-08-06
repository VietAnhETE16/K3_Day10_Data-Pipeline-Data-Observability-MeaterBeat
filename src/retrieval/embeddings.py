from __future__ import annotations

import os
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv()


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        # We use text-embedding-3-small as the default OpenAI embedding model
        # to avoid dependencies on local sentence-transformers models.
        self.model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.model.embed_query(text)
