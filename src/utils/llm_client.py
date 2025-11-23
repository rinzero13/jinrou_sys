import os
import json
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI # 例としてOpenAIを使用
from .prompt_manager import PromptManager # 新規追加

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        # ... 既存の初期化
        self.model = "gpt-4o-mini"
        self.prompt_manager = PromptManager() # 新規追加: PromptManagerのインスタンス化

    def generate_response(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> Dict[str, Any]:
        """LLMにプロンプトを送信し、応答を取得する"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = {"type": "json_object"} if json_mode else {"type": "text"}
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format=response_format,
                temperature=0.7, # 発話生成は高め、判定は低めが推奨
            )
            
            content = response.choices[0].message.content
            if json_mode:
                return json.loads(content)
            return {"text": content}
            
        except Exception as e:
            logger.error(f"LLM APIエラー: {e}")
            return {"error": str(e), "text": "Skip"} # エラー時はスキップ相当の値を返す

# PromptManagerのメソッドをラップして利用可能にする
    def get_generation_prompt(*args, **kwargs) -> str:
        return self.prompt_manager.get_generation_prompt(*args, **kwargs)

    def get_consistency_check_prompt(*args, **kwargs) -> str:
        return self.prompt_manager.get_consistency_check_prompt(*args, **kwargs)

    def get_regeneration_prompt(*args, **kwargs) -> str:
        return self.prompt_manager.get_regeneration_prompt(*args, **kwargs)