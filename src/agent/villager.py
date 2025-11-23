"""Module that defines the Villager agent class.

村人のエージェントクラスを定義するモジュール.
"""

from __future__ import annotations

from typing import Any

from aiwolf_nlp_common.packet import Role

from agent.agent import Agent


class Villager(Agent):
    """Villager agent class.

    村人のエージェントクラス.
    """

    def __init__(
        self,
        config: dict[str, Any],
        name: str,
        game_id: str,
        role: Role,  # noqa: ARG002
    ) -> None:
        """Initialize the villager agent.

        村人のエージェントを初期化する.

        Args:
            config (dict[str, Any]): Configuration dictionary / 設定辞書
            name (str): Agent name / エージェント名
            game_id (str): Game ID / ゲームID
            role (Role): Role (ignored, always set to VILLAGER) / 役職(無視され、常にVILLAGERに設定)
        """
        super().__init__(config, name, game_id, Role.VILLAGER)

# src/agent/villager.py の talk() メソッドをオーバーライド

    def talk(self) -> str:
            """LLMを用いてトークリクエストに対する応答を返す。"""
            # 村人陣営の目標
            goal = "人狼を吊り、村人陣営の勝利に貢献すること。"
            
            # _generate_llm_utterance の呼び出し
            return self._generate_llm_utterance(
                role_goal=goal,
                is_deceptive_context=False,
                is_whisper=False
            )
    
    def vote(self) -> str:
        """Return response to vote request.

        投票リクエストに対する応答を返す.

        Returns:
            str: Agent name to vote / 投票対象のエージェント名
        """
        return super().vote()
