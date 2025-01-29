import openai
import httpx
import os

from app.schemas.ai import AIMessageSchema

openai.api_key = os.getenv("OPENAI_API_KEY")


class AIRepository:
    def __init__(self):
        self.client = openai.AsyncOpenAI()

    async def generate(self, messages: list[AIMessageSchema]):
        print("history:", [msg.model_dump() for msg in messages])
        completion = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": "You are a helpful assistant."},
            ] + [msg.model_dump() for msg in messages]
        )
        print("Generated:", completion.choices)
        return completion.choices[0].message.content

