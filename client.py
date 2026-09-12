import asyncio
import json
import os

from openai import OpenAI
from mcp import Client
from server import mcp


client_openai = OpenAI()


async def ask_mcp(question: str):
    async with Client(mcp) as client:
        tools = await client.list_tools()

        openai_tools = []

        for tool in tools.tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema,
                    },
                }
            )

        response = client_openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ],
            tools=openai_tools
        )

        tool_call = response.choices[0].message.tool_calls[0]

        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        tool_result = await client.call_tool(
            tool_name,
            tool_args
        )

        tool_output = tool_result.content[0].text

        final_response = client_openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": question
                },
                response.choices[0].message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output
                }
            ]
        )

        return final_response.choices[0].message.content

async def main():
    answer = await ask_mcp(
        r"C:\python\MCP の中から、MCPという文字を含む行を探してください。"
    )

    print(answer)

asyncio.run(main())