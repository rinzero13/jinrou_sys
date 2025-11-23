"""Module that defines the Werewolf agent class.

人狼のエージェントクラスを定義するモジュール.
"""

from __future__ import annotations

from typing import Any

from aiwolf_nlp_common.packet import Role

from agent.agent import Agent


class Werewolf(Agent):
    """Werewolf agent class.

    人狼のエージェントクラス.
    """

    def __init__(
        self,
        config: dict[str, Any],
        name: str,
        game_id: str,
        role: Role,  # noqa: ARG002
    ) -> None:
        """Initialize the werewolf agent.

        人狼のエージェントを初期化する.

        Args:
            config (dict[str, Any]): Configuration dictionary / 設定辞書
            name (str): Agent name / エージェント名
            game_id (str): Game ID / ゲームID
            role (Role): Role (ignored, always set to WEREWOLF) / 役職(無視され、常にWEREWOLFに設定)
        """
        super().__init__(config, name, game_id, Role.WEREWOLF)

# src/agent/werewolf.py の talk() と whisper() メソッドをオーバーライド

    def talk(self) -> str:
        """LLMを用いてトークリクエストに対する応答を返す（嘘を含む可能性あり）。"""
        # 人狼陣営の目標
        goal = "自分の人狼であることを隠し、村人陣営を欺き、人狼陣営の勝利に貢献すること。"
        
        return self._generate_llm_utterance(
            role_goal=goal,
            is_deceptive_context=True, # 嘘戦略を許可
            is_whisper=False
        )

    def whisper(self) -> str:
        """LLMを用いて囁きリクエストに対する応答を返す（真実）。"""
        # 人狼間の会話なので、真実（嘘ではない）を話す
        goal = "仲間と連携し、襲撃対象の選定や村人陣営の撹乱戦略を話し合うこと。"
        
        return self._generate_llm_utterance(
            role_goal=goal,
            is_deceptive_context=False, # 嘘戦略は行わない
            is_whisper=True
        )

    def attack(self) -> str:
        """襲撃リクエストに対する応答を返す（最新の戦略に基づいて決定）。"""
        # 投票・能力行使のロジックは、最新の発話生成で決定された戦略の核を利用する
        if self.latest_strategy_core and 'target_attack' in self.latest_strategy_core:
            target_name = self.latest_strategy_core['target_attack']
            if target_name in self.get_alive_agents():
                return target_name
        
        # 戦略の核が利用できない場合は、フォールバック（既存のランダム選択など）
        return super().attack()

    def vote(self) -> str:
        """Return response to vote request.

        投票リクエストに対する応答を返す.

        Returns:
            str: Agent name to vote / 投票対象のエージェント名
        """
        return super().vote()
