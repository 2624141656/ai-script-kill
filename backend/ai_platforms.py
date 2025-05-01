from typing import Dict, Any, Optional
import os
from openai import AsyncOpenAI
import aiohttp
import json

class AIPlatform:
    def __init__(self, name: str, api_key: str, api_endpoint: str, model: str):
        self.name = name
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model

class OpenAIPlatform(AIPlatform):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("警告：未设置 OPENAI_API_KEY 环境变量，将使用默认值")
            api_key = "default_key"
            
        super().__init__(
            name="OpenAI",
            api_key=api_key,
            api_endpoint="https://api.openai.com/v1",
            model="gpt-4"
        )
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate_response(self, messages: list, temperature: float = 0.7) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content

class ClaudePlatform(AIPlatform):
    def __init__(self):
        super().__init__(
            name="Claude",
            api_key=os.getenv("CLAUDE_API_KEY"),
            api_endpoint="https://api.anthropic.com/v1",
            model="claude-3-opus-20240229"
        )

    async def generate_response(self, messages: list, temperature: float = 0.7) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # 转换消息格式
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                claude_messages.append({"role": "assistant", "content": msg["content"]})
            else:
                claude_messages.append(msg)
        
        data = {
            "model": self.model,
            "messages": claude_messages,
            "temperature": temperature
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_endpoint}/messages",
                headers=headers,
                json=data
            ) as response:
                result = await response.json()
                return result["content"][0]["text"]

class GeminiPlatform(AIPlatform):
    def __init__(self):
        super().__init__(
            name="Gemini",
            api_key=os.getenv("GEMINI_API_KEY"),
            api_endpoint="https://generativelanguage.googleapis.com/v1",
            model="gemini-pro"
        )

    async def generate_response(self, messages: list, temperature: float = 0.7) -> str:
        headers = {
            "x-goog-api-key": self.api_key,
            "content-type": "application/json"
        }
        
        # 转换消息格式
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
            else:
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
        
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_endpoint}/models/{self.model}:generateContent",
                headers=headers,
                json=data
            ) as response:
                result = await response.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]

class AIPlatformManager:
    def __init__(self):
        self.platforms = {
            "openai": OpenAIPlatform(),
            "claude": ClaudePlatform(),
            "gemini": GeminiPlatform()
        }

    def get_platform(self, platform_name: str) -> Optional[AIPlatform]:
        return self.platforms.get(platform_name)

    async def generate_response(self, platform_name: str, messages: list, temperature: float = 0.7) -> str:
        platform = self.get_platform(platform_name)
        if not platform:
            raise ValueError(f"Unknown AI platform: {platform_name}")
        
        return await platform.generate_response(messages, temperature) 