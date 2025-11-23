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
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )
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
                temperature=0.7,
            )
            
            content = response.choices[0].message.content
            if json_mode:
                # ログを追加して、JSONパース前のコンテンツを確認できるようにする
                logger.debug(f"Received JSON content: {content[:50]}...")
                return json.loads(content) 
            return {"text": content}
            
        except json.JSONDecodeError as json_e:
            logger.error(f"LLM APIから無効なJSON応答: {json_e}")
            # エージェントログには、デバッグのために応答の最初の部分を含める
            return {"error": f"Invalid JSON: {str(json_e)}", "text": "Skip"}
            
        except Exception as e:
            # ログのレベルを警告からエラーに変更し、より目立たせる
            logger.error(f"LLM APIエラーによりクラッシュ: {e}", exc_info=True) # exc_info=Trueでスタックトレースを出力
            # エラー発生を明確に示し、エージェントがこれを受け取る
            return {"error": str(e), "text": "Skip"}

# PromptManagerのメソッドをラップして利用可能にする
    def get_generation_prompt(self, *args, **kwargs) -> str: # self を追加
        return self.prompt_manager.get_generation_prompt(*args, **kwargs)

    def get_consistency_check_prompt(self, *args, **kwargs) -> str: # self を追加
        return self.prompt_manager.get_consistency_check_prompt(*args, **kwargs)

    def get_regeneration_prompt(self, *args, **kwargs) -> str: # self を追加
        return self.prompt_manager.get_regeneration_prompt(*args, **kwargs)