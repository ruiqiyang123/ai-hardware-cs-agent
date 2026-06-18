from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from model.factory import chat_model
from agent.tools.agent_tools import (rag_summarize, get_weather, get_user_location, get_user_id,
                                     get_current_month, fetch_external_data, fill_context_for_report)
from agent.tools.middleware import build_agent_prompt


class ReactAgent:
    def __init__(self):
        self.agent = create_react_agent(
            model=chat_model,
            tools=[rag_summarize, get_weather, get_user_location, get_user_id,
                   get_current_month, fetch_external_data, fill_context_for_report],
            prompt=build_agent_prompt,
            version="v2",
        )

    def execute_stream(self, query: str):
        input_dict = {
            "messages": [
                {"role": "user", "content": query},
            ]
        }

        seen_message_ids = set()
        for chunk in self.agent.stream(input_dict, stream_mode="values"):
            latest_message = chunk["messages"][-1]
            message_id = getattr(latest_message, "id", None)
            if (
                    isinstance(latest_message, AIMessage)
                    and latest_message.content
                    and message_id not in seen_message_ids
            ):
                seen_message_ids.add(message_id)
                yield latest_message.content.strip() + "\n"


if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)
