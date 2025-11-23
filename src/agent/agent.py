"""Module that defines the base class for agents.

エージェントの基底クラスを定義するモジュール.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, Optional, Dict 
import json # JSON処理のために必要
from aiwolf_nlp_common.packet import Info, Packet, Request, Role, Setting, Status, Talk, Species

from utils.agent_logger import AgentLogger
from utils.stoppable_thread import StoppableThread
from utils.llm_client import LLMClient # 新規追加

if TYPE_CHECKING:
    from collections.abc import Callable

P = ParamSpec("P")
T = TypeVar("T")


class Agent:
    """Base class for agents.

    エージェントの基底クラス.
    """

    def __init__(
        self,
        config: dict[str, Any],
        name: str,
        game_id: str,
        role: Role,
    ) -> None:
        """Initialize the agent.

        エージェントの初期化を行う.

        Args:
            config (dict[str, Any]): Configuration dictionary / 設定辞書
            name (str): Agent name / エージェント名
            game_id (str): Game ID / ゲームID
            role (Role): Role / 役職
        """
        self.config = config
        self.agent_name = name
        self.agent_logger = AgentLogger(config, name, game_id)
        self.request: Request | None = None
        self.info: Info | None = None
        self.setting: Setting | None = None
        self.talk_history: list[Talk] = []
        self.whisper_history: list[Talk] = []
        self.role = role

        self.llm_client = LLMClient() # LLMクライアントのインスタンス化
        self.latest_strategy_core: Optional[Dict[str, Any]] = None # 最新の戦略の核を保持

        self.comments: list[str] = []
        with Path.open(
            Path(str(self.config["path"]["random_talk"])),
            encoding="utf-8",
        ) as f:
            self.comments = f.read().splitlines()

    @staticmethod
    def timeout(func: Callable[P, T]) -> Callable[P, T]:
        """Decorator to set action timeout.

        アクションタイムアウトを設定するデコレータ.

        Args:
            func (Callable[P, T]): Function to be decorated / デコレート対象の関数

        Returns:
            Callable[P, T]: Function with timeout functionality / タイムアウト機能を追加した関数
        """

        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            res: T | Exception = Exception("No result")

            def execute_with_timeout() -> None:
                nonlocal res
                try:
                    res = func(*args, **kwargs)
                except Exception as e:  # noqa: BLE001
                    res = e

            thread = StoppableThread(target=execute_with_timeout)
            thread.start()
            self = args[0] if args else None
            if not isinstance(self, Agent):
                raise TypeError(self, " is not an Agent instance")
            timeout_value = (self.setting.timeout.action if hasattr(self, "setting") and self.setting else 0) // 1000
            if timeout_value > 0:
                thread.join(timeout=timeout_value)
                if thread.is_alive():
                    self.agent_logger.logger.warning(
                        "アクションがタイムアウトしました: %s",
                        self.request,
                    )
                    if bool(self.config["agent"]["kill_on_timeout"]):
                        thread.stop()
                        self.agent_logger.logger.warning(
                            "アクションを強制終了しました: %s",
                            self.request,
                        )
            else:
                thread.join()
            if isinstance(res, Exception):  # type: ignore[arg-type]
                raise res
            return res

        return _wrapper

    def set_packet(self, packet: Packet) -> None:
        """Set packet information.

        パケット情報をセットする.

        Args:
            packet (Packet): Received packet / 受信したパケット
        """
        self.request = packet.request
        if packet.info:
            self.info = packet.info
        if packet.setting:
            self.setting = packet.setting
        if packet.talk_history:
            self.talk_history.extend(packet.talk_history)
        if packet.whisper_history:
            self.whisper_history.extend(packet.whisper_history)
        if self.request == Request.INITIALIZE:
            self.talk_history: list[Talk] = []
            self.whisper_history: list[Talk] = []
        self.agent_logger.logger.debug(packet)

    def get_alive_agents(self) -> list[str]:
        """Get the list of alive agents.

        生存しているエージェントのリストを取得する.

        Returns:
            list[str]: List of alive agent names / 生存エージェント名のリスト
        """
        if not self.info:
            return []
        return [k for k, v in self.info.status_map.items() if v == Status.ALIVE]

    def name(self) -> str:
        """Return response to name request.

        名前リクエストに対する応答を返す.

        Returns:
            str: Agent name / エージェント名
        """
        return self.agent_name

    def initialize(self) -> None:
        """Perform initialization for game start request.

        ゲーム開始リクエストに対する初期化処理を行う.
        """

    def daily_initialize(self) -> None:
        """Perform processing for daily initialization request.

        昼開始リクエストに対する処理を行う.
        """

    def whisper(self) -> str:
        """Return response to whisper request.

        囁きリクエストに対する応答を返す.

        Returns:
            str: Whisper message / 囁きメッセージ
        """
        return random.choice(self.comments)  # noqa: S311

    def talk(self) -> str:
        """Return response to talk request.

        トークリクエストに対する応答を返す.

        Returns:
            str: Talk message / 発言メッセージ
        """
        return random.choice(self.comments)  # noqa: S311

    def daily_finish(self) -> None:
        """Perform processing for daily finish request.

        昼終了リクエストに対する処理を行う.
        """

    def divine(self) -> str:
        """Return response to divine request.

        占いリクエストに対する応答を返す.

        Returns:
            str: Agent name to divine / 占い対象のエージェント名
        """
        return random.choice(self.get_alive_agents())  # noqa: S311

    def guard(self) -> str:
        """Return response to guard request.

        護衛リクエストに対する応答を返す.

        Returns:
            str: Agent name to guard / 護衛対象のエージェント名
        """
        return random.choice(self.get_alive_agents())  # noqa: S311

# src/agent/agent.py の vote() メソッドをオーバーライド

    def vote(self) -> str:
        """投票リクエストに対する応答を返す（最新の戦略に基づいて決定）。"""
        # 最新の戦略の核に投票対象が含まれていれば、それを使用
        if self.latest_strategy_core and 'target_vote' in self.latest_strategy_core:
            target_name = self.latest_strategy_core['target_vote']
            # 対象が生存しているかチェック
            if target_name in self.get_alive_agents():
                return target_name
        
        # 戦略の核がない、または無効な場合は、ランダム（既存のロジック）
        return random.choice(self.get_alive_agents())

    def attack(self) -> str:
        """Return response to attack request.

        襲撃リクエストに対する応答を返す.

        Returns:
            str: Agent name to attack / 襲撃対象のエージェント名
        """
        return random.choice(self.get_alive_agents())  # noqa: S311

    def finish(self) -> None:
        """Perform processing for game finish request.

        ゲーム終了リクエストに対する処理を行う.
        """

# src/agent/agent.py の変更 (Agentクラスの任意の場所に追加)

    def _get_objective_facts(self) -> str:
        """ゲームの客観的事実（吊り、襲撃、真結果など）を整形して返す。"""
        if not self.info:
            return "現在、確定している客観的事実はありません。"
            
        facts = []
        
        # 過去の処刑結果
        if self.info.executed_agent:
            facts.append(f"Day {self.info.day-1}の投票により、{self.info.executed_agent}が処刑されました。")
        
        # 過去の襲撃結果
        if self.info.attacked_agent:
            facts.append(f"Night {self.info.day-1}の夜に、{self.info.attacked_agent}が襲撃されました。")

        # 生存者リスト
        alive_agents = [name for name, status in self.info.status_map.items() if status == Status.ALIVE]
        facts.append(f"現在の生存者は {len(alive_agents)}人 ({', '.join(alive_agents)})です。")
        
        # 自分の確定情報 (占い師/霊媒師のみ)
        if self.role == Role.SEER and self.info.divine_result:
            res = self.info.divine_result
            facts.append(f"Day {res.day}に{res.target}を占った結果、種族は{res.result}でした。")
        
        if self.role == Role.MEDIUM and self.info.medium_result:
            res = self.info.medium_result
            facts.append(f"Day {res.day}の処刑者({res.target})の霊能結果は、種族が{res.result}でした。")
            
        return "\n".join(facts)
        
    def _get_utterance_history_json(self) -> str:
        """過去の発言履歴をJSON文字列として返す。"""
        # トークと囁きを統合し、LLMに渡す
        history = []
        for talk in self.talk_history:
            history.append({
                "day": talk.day,
                "agent": talk.agent,
                "text": talk.text,
                "type": "Talk"
            })
        # 囁きは人狼のみに公開される情報なので、人狼の場合のみ含める
        if self.role == Role.WEREWOLF:
            for whisper in self.whisper_history:
                 history.append({
                    "day": whisper.day,
                    "agent": whisper.agent,
                    "text": whisper.text,
                    "type": "Whisper"
                })
        
        # 辞書順で並べ替える（日付→発言ターン順）
        history.sort(key=lambda x: (x['day'], x.get('turn', 0)))

        return json.dumps(history, indent=2, ensure_ascii=False)


# src/agent/agent.py の Agent クラス内にメソッドとして追加

MAX_REGENERATION_ATTEMPTS = 3 # 再生成の最大試行回数

    def _generate_llm_utterance(self, role_goal: str, is_deceptive_context: bool, is_whisper: bool = False) -> str:
        """LLMを用いて発話を生成し、論理的一貫性をチェックし、修正するループ。"""
        
        if not self.info:
            return "Skip"
            
        # 1. データ準備
        objective_facts = self._get_objective_facts()
        utterance_history_json = self._get_utterance_history_json()
        
        current_utterance_text = "Skip"
        self.latest_strategy_core = None
        
        # 最初の発話生成
        # LLMクライアントのメソッド名は仮です。ステップ1.2のコメントで示したように、
        # 実際にはプロンプトテンプレートを管理するクラス/ファイルが必要です。
        generation_prompt = self.llm_client.get_generation_prompt(
            self.role.name, 
            role_goal, 
            self.agent_name, 
            is_deceptive_context,
            is_whisper,
            objective_facts,
            utterance_history_json,
            # その他、生存者リストなど必要な情報
        )
        
        generation_result = self.llm_client.generate_response(
            system_prompt=f"あなたは人狼ゲームのエージェント（役職:{self.role.name}）です。",
            user_prompt=generation_prompt,
            json_mode=True
        )
        
        if "error" in generation_result:
            return "Skip" 

        current_utterance_text = generation_result.get("utterance", "Skip")
        self.latest_strategy_core = generation_result.get("core_strategy", {})

        # 2. 論理チェックと修正のループ
        for attempt in range(MAX_REGENERATION_ATTEMPTS):
            
            # 2.1. 論理判定の実行
            consistency_prompt = self.llm_client.get_consistency_check_prompt(
                self.agent_name,
                self.role.name,
                current_utterance_text,
                objective_facts,
                utterance_history_json
            )
            
            check_result = self.llm_client.generate_response(
                system_prompt="あなたは発話の論理的矛盾を判定する専門家です。",
                user_prompt=consistency_prompt,
                json_mode=True
            )
            
            # 2.2. 結果の判定と処理
            is_consistent = check_result.get("is_consistent", False)
            if is_consistent:
                # 矛盾なし: 採用してループを抜ける
                # logger.info(f"発話生成に成功 (試行{attempt+1}回): {current_utterance_text}")
                return current_utterance_text
            
            # 矛盾あり: 修正指示を生成し、再生成へ
            contradiction_type = check_result.get("contradiction_type", "不明な矛盾")
            reasoning = check_result.get("reasoning", "詳細な理由が不明です。")
            # logger.warning(f"矛盾検出 (試行{attempt+1}回): {contradiction_type}, 理由: {reasoning}")
            
            # 再生成プロンプトの作成（矛盾の理由と修正指示をフィードバック）
            regeneration_prompt = self.llm_client.get_regeneration_prompt(
                current_utterance_text,
                contradiction_type,
                reasoning
            )
            
            regeneration_result = self.llm_client.generate_response(
                system_prompt="あなたは論理的矛盾を修正するエージェントです。",
                user_prompt=regeneration_prompt,
                json_mode=True
            )
            
            # 修正された発話案を取得
            current_utterance_text = regeneration_result.get("utterance", "Skip")
            if current_utterance_text == "Skip":
                break

        # 3. 最大試行回数を超えた場合
        # logger.error(f"発話生成が最大試行回数 ({MAX_REGENERATION_ATTEMPTS})を超えて失敗しました。")
        return "Skip"

    @timeout
    def action(self) -> str | None:  # noqa: C901, PLR0911
        """Execute action according to request type.

        リクエストの種類に応じたアクションを実行する.

        Returns:
            str | None: Action result string or None / アクションの結果文字列またはNone
        """
        match self.request:
            case Request.NAME:
                return self.name()
            case Request.TALK:
                return self.talk()
            case Request.WHISPER:
                return self.whisper()
            case Request.VOTE:
                return self.vote()
            case Request.DIVINE:
                return self.divine()
            case Request.GUARD:
                return self.guard()
            case Request.ATTACK:
                return self.attack()
            case Request.INITIALIZE:
                self.initialize()
            case Request.DAILY_INITIALIZE:
                self.daily_initialize()
            case Request.DAILY_FINISH:
                self.daily_finish()
            case Request.FINISH:
                self.finish()
            case _:
                pass
        return None
