# src/utils/prompt_manager.py (新規作成)

from typing import Dict, Any, List

class PromptManager:
    def __init__(self):
        # ゲームルールはプロンプトに埋め込むため、ここでテキストとして保持
        self.GAME_RULES = """
        人狼ゲームの基本ルールは以下の通りです。
        1. 役職: 人狼、狂人（人狼陣営）、占い師、騎士、村人（村人陣営）など。
        2. 勝利条件: 村人陣営は全ての人狼を排除。人狼陣営は生存者が同数以下になること。
        3. 占い師は夜に1人占え、種族（人狼/人間）を知る。
        4. 狂人は人狼を知らないが、人狼陣営の勝利を目指す。
        5. 嘘をつくことは全ての役職に許容される戦略である。
        """

    def get_generation_prompt(self, role: str, goal: str, agent_name: str, 
                              is_deceptive: bool, is_whisper: bool, 
                              facts: str, history_json: str) -> str:
        """ステップ2: 仮想発話（発言案）と戦略の核を生成するプロンプト"""
        context = "嘘をつくことは許可されています。" if is_deceptive else "真実のみを発言してください。"
        target_field = "target_attack" if is_whisper else "target_vote"
        
        return f"""
        あなたは人狼ゲームのエージェント（{role}）です。
        あなたの目標は「{goal}」です。現在のゲーム状況に基づき、発言内容（utterance）と、その発言に紐づく行動戦略の核（core_strategy）をJSON形式で生成してください。
        
        **【行動制約】**
        - {context}
        - 発言は{agent_name}視点で行ってください。
        
        **【入力情報】**
        - **客観的事実:** {facts}
        - **発話履歴:** {history_json}
        
        **【出力JSON形式】**
        {{
            "utterance": "生成した発言内容（例: 私は〇〇さんを信じます）",
            "core_strategy": {{
                "strategy_summary": "この発言の意図（例: 〇〇を吊り対象に誘導する）",
                "{target_field}": "戦略的に行動したい対象（Agent[XX]形式）"
            }}
        }}
        """

    def get_consistency_check_prompt(self, speaker: str, role: str, utterance: str, facts: str, history_json: str) -> str:
        """ステップ3: 生成された発話が論理的に矛盾しないかをチェックするプロンプト"""
        # ゼミ資料（Page 30-33）の3つの矛盾軸を反映させる
        
        return f"""
        あなたは人狼ゲームの発言を分析する専門家です。以下の発言が「客観的事実」「発話者の役職・行動」「他のプレイヤーの発話」と矛盾しないか評価してください。
        
        **【評価対象】**
        - **発話者:** {speaker} (役職: {role})
        - **発話内容:** {utterance}
        
        **【参照情報】**
        - **ゲームの客観的事実:** {facts}
        - **発話履歴（他のプレイヤーの発話）:** {history_json}
        - **基本ルール:** {self.GAME_RULES}

        **【判定基準】**
        1. **客観的事実との矛盾:** 発言が、既に確定した情報やゲームルールに反していないか。
        2. **役職・行動との矛盾:** 発話者の役職（特に嘘が戦略的でない場合）や過去の行動と矛盾していないか。（人狼の嘘は戦略的であれば矛盾「なし」と判定）
        3. **他のプレイヤーの発話との関係:** 直前の発話に対する応答として適切で論理的か。
        
        **【出力JSON形式】**
        {{
            "is_consistent": true or false,
            "reasoning": "矛盾を検出した場合はその詳細な理由と、どの矛盾タイプに該当するかを記述。",
            "contradiction_type": "なし" | "客観的事実との矛盾" | "発話者の行動・役職との矛盾" | "他プレイヤーの発話との矛盾"
        }}
        """

    def get_regeneration_prompt(self, old_utterance: str, contradiction_type: str, reasoning: str) -> str:
        """矛盾が検出された場合に、発話を修正させるプロンプト"""
        return f"""
        以前、あなたは以下の発言を生成しましたが、論理的な矛盾が検出されました。
        
        **【検出された矛盾】**
        - **タイプ:** {contradiction_type}
        - **理由:** {reasoning}
        
        この矛盾点を解消するように発言内容を修正し、修正後の発言内容（utterance）のみを含むJSON形式で再生成してください。
        
        **【修正前の発言】**
        {old_utterance}
        
        **【出力JSON形式】**
        {{
            "utterance": "修正後の発言内容"
        }}
        """