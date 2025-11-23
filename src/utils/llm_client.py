import os
import json
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI # 例としてOpenAIを使用

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        # APIキーは環境変数から読み込むことを推奨
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini" # 使用するLLMモデル名

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

# 補足: プロンプトテンプレートは別ファイルで管理することを推奨します。
# (例: src/utils/prompt_templates.py)