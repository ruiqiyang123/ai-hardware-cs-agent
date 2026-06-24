
"""
总结服务类：用户提问，搜索参考资料，将提问和参考资料提交给模型，让模型总结回复。

改造点：增加引用溯源——在答案末尾标注命中的知识库文档来源，提升回答可信度。
原版本只返回模型总结后的答案，用户无法判断依据；售后场景用户对 AI 回答信任度低，
加来源标注后，用户可以追溯答案出处。
"""
import os
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser

from rag.vector_store import VectorStoreService
from utils.prompt_loader import load_rag_prompts
from langchain_core.prompts import PromptTemplate
from model.factory import chat_model
from utils.logger_handler import logger


def _extract_source_name(metadata: dict) -> str:
    """从文档元数据中提取人类可读的来源名（文件名）。

    LangChain 加载文档时，metadata['source'] 通常是文件绝对路径，
    这里只取文件名展示给用户。
    """
    source = metadata.get("source", "未知来源")
    # source 可能是路径，取文件名
    if source and os.sep in source:
        source = source.rsplit(os.sep, 1)[-1]
    elif "/" in source:
        source = source.rsplit("/", 1)[-1]
    return source


class RagSummarizeService:
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.retriever = self.vector_store.get_retriever()
        self.prompt_text = load_rag_prompts()
        self.prompt_template = PromptTemplate.from_template(self.prompt_text)
        self.model = chat_model
        self.chain = self._init_chain()

    def _init_chain(self):
        return self.prompt_template | self.model | StrOutputParser()

    def retriever_docs(self, query: str) -> list[Document]:
        return self.retriever.invoke(query)

    def rag_summarize(self, query: str) -> str:
        context_docs = self.retriever_docs(query)

        if not context_docs:
            logger.warning(f"[rag_summarize]未检索到相关资料，query={query}")
            return f"知识库中未检索到与「{query}」相关的内容，无法生成准确答复。"

        context = ""
        sources = []
        counter = 0
        for doc in context_docs:
            counter += 1
            context += f"【参考资料{counter}】: 参考资料：{doc.page_content} | 参考元数据：{doc.metadata}\n"
            sources.append(_extract_source_name(doc.metadata))

        answer = self.chain.invoke(
            {
                "input": query,
                "context": context,
            }
        )

        # 引用溯源：去重后把来源文件名附在答案末尾
        unique_sources = []
        for s in sources:
            if s not in unique_sources:
                unique_sources.append(s)

        source_line = "\n\n📚 参考来源：" + "、".join(unique_sources)
        logger.info(f"[rag_summarize]query={query}，命中来源={unique_sources}")
        return answer + source_line


if __name__ == '__main__':
    rag = RagSummarizeService()

    print(rag.rag_summarize("小户型适合哪些扫地机器人"))
