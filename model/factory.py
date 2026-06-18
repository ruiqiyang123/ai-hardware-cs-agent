from abc import ABC, abstractmethod
import os
from typing import Optional, Union

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI
from model.local_embeddings import LocalHashEmbeddings
from utils.config_handler import rag_conf


load_dotenv()


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Union[Embeddings, BaseChatModel]]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Union[Embeddings, BaseChatModel]]:
        provider = os.getenv("CHAT_PROVIDER", "dashscope").lower()
        if provider in {"mimo", "openai"}:
            api_key = os.getenv("MIMO_API_KEY") or os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("MIMO_BASE_URL") or os.getenv("OPENAI_BASE_URL")
            model_name = (
                os.getenv("MIMO_CHAT_MODEL")
                or os.getenv("OPENAI_CHAT_MODEL")
                or rag_conf["chat_model_name"]
            )
            if not api_key or not base_url:
                raise ValueError("使用 MiMo/OpenAI 兼容模型时，请配置 MIMO_API_KEY 和 MIMO_BASE_URL")
            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=float(os.getenv("CHAT_TEMPERATURE", "0")),
            )

        return ChatTongyi(model=rag_conf["chat_model_name"])


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Union[Embeddings, BaseChatModel]]:
        provider = os.getenv("EMBEDDING_PROVIDER", "dashscope").lower()
        if provider == "local":
            dimension = int(os.getenv("LOCAL_EMBEDDING_DIMENSION", "384"))
            return LocalHashEmbeddings(dimension=dimension)

        return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])


chat_model = ChatModelFactory().generator()

embed_model = EmbeddingsFactory().generator()
