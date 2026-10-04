import asyncio
import json
from pathlib import Path

from mcp import Client
from openai import OpenAI

from server import mcp


MODEL = "gpt-4.1-mini"
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

openai_client = OpenAI()


def convert_mcp_tools_to_openai(mcp_tools) -> list[dict]:
    """MCPのTool定義をOpenAI Function Calling形式へ変換する。"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in mcp_tools
    ]


async def ask_mcp(question: str) -> str:
    """LLMがToolを選択し、MCP Client経由でServer側Toolを実行して最終回答を返す。"""

    async with Client(mcp) as mcp_client:
        # MCP Serverが公開しているTool定義を取得する
        tools_response = await mcp_client.list_tools()

        # OpenAI Function Calling形式へ変換する
        openai_tools = convert_mcp_tools_to_openai(tools_response.tools)

        # 質問内容とTool定義をもとに、LLMが利用するToolを判断する
        first_response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": question},
            ],
            tools=openai_tools,
        )

        assistant_message = first_response.choices[0].message

        # Tool利用が不要な場合はLLMの応答をそのまま返す
        if not assistant_message.tool_calls:
            return assistant_message.content or ""

        # この実装では先頭のTool呼び出しを処理する
        tool_call = assistant_message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        # MCP Client経由でServer側のToolを実行する
        tool_result = await mcp_client.call_tool(tool_name, tool_args)
        tool_output = tool_result.content[0].text

        # Toolの実行結果をLLMへ返し、ユーザー向けの最終回答を生成する
        final_response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": question},
                assistant_message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                },
            ],
        )

        return final_response.choices[0].message.content or ""


async def main() -> None:
    question = (
        f"{DATA_DIR} の中から、MCPという文字を含む行を探してください。"
    )

    answer = await ask_mcp(question)
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
