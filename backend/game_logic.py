from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from models import GameSession, Script
from ai_service import AIService
from fastapi import HTTPException

class GameManager:
    def __init__(self, db: AsyncSession, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
        self.active_games = {}

    async def run_game_session(self, session_id: str):
        """运行游戏会话的主循环"""
        session = await self.db.get(GameSession, session_id)
        if not session:
            return

        script = await self.db.get(Script, session.script_id)
        script_data = json.loads(script.content)
        
        # 初始化游戏
        await self.initialize_game(session, script_data)
        
        # 游戏主循环
        while session.status == "active":
            # 根据游戏阶段处理
            if session.phase == "discussion":
                await self.handle_discussion_phase(session, script_data)
            elif session.phase == "voting":
                await self.handle_voting_phase(session)
            elif session.phase == "result":
                await self.handle_result_phase(session, script_data)
            
            await self.db.commit()
            await asyncio.sleep(1)  # 防止CPU占用过高

    async def initialize_game(self, session: GameSession, script_data: Dict[str, Any]):
        """初始化游戏"""
        # 设置初始阶段
        session.phase = "preparation"
        session.round_number = 0
        session.discovered_clues = []
        session.votes = {}
        session.player_states = {}
        
        # 初始化系统消息
        initial_message = {
            "sender": "system",
            "content": f"游戏开始！剧本：{script_data['title']}\n背景：{script_data['background']}",
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages.append(initial_message)
        
        # 分配角色和初始化玩家状态
        characters = script_data["characters"]
        for i, participant in enumerate(session.participants):
            if i < len(characters):
                character = characters[i]
                role_message = {
                    "sender": "system",
                    "content": f"{participant} 扮演角色：{character['name']}\n背景：{character['background']}\n动机：{character['motive']}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                session.messages.append(role_message)
                
                # 初始化玩家状态
                session.player_states[participant] = {
                    "character": character["name"],
                    "skills": character.get("skills", {}),
                    "used_skills": set()
                }
        
        await self.db.commit()

    async def handle_discussion_phase(self, session: GameSession, script_data: Dict[str, Any]):
        """处理讨论阶段"""
        if not session.current_speaker:
            session.current_speaker = session.participants[0]
        
        # 如果当前发言者是AI
        if session.current_speaker.startswith("ai_"):
            # 构建AI的上下文
            context = self.build_ai_context(session, session.current_speaker, script_data)
            
            # 生成AI响应
            response = await self.ai_service.generate_response(
                session.id,
                "请根据当前局势和你的角色发表看法",
                context=context
            )
            
            # 记录AI的发言
            ai_message = {
                "sender": session.current_speaker,
                "content": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            session.messages.append(ai_message)
            
            # 更新下一个发言者
            current_index = session.participants.index(session.current_speaker)
            next_index = (current_index + 1) % len(session.participants)
            session.current_speaker = session.participants[next_index]

    async def handle_voting_phase(self, session: GameSession):
        """处理投票阶段"""
        # 如果是AI的投票回合
        for participant in session.participants:
            if participant.startswith("ai_") and participant not in session.votes:
                # AI进行投票
                vote_target = await self.ai_service.generate_response(
                    session.id,
                    "请根据当前局势选择一个投票目标",
                    context=session.messages[-10:]  # 使用最近的消息作为上下文
                )
                
                # 确保投票目标有效
                if vote_target in session.participants:
                    session.votes[participant] = vote_target

    async def handle_result_phase(self, session: GameSession, script_data: Dict[str, Any]):
        """处理结果阶段"""
        # 检查是否有足够的线索被发现
        if len(session.discovered_clues) >= len(script_data["clues"]) * 0.7:  # 70%的线索被发现
            # 进入最终投票
            if not session.votes:
                result_message = {
                    "sender": "system",
                    "content": "已发现足够的线索，进入最终投票阶段！",
                    "timestamp": datetime.utcnow().isoformat()
                }
                session.messages.append(result_message)
            elif len(session.votes) == len(session.participants):
                # 所有人都已投票，结束游戏
                await self.end_game(session)

    async def handle_skill_use(self, session: GameSession, user: str, skill_name: str, target: str = None) -> Dict[str, Any]:
        """处理技能使用"""
        player_state = session.player_states.get(user, {})
        skills = player_state.get("skills", {})
        
        if skill_name not in skills:
            raise HTTPException(status_code=400, detail="Skill not available")
        
        skill = skills[skill_name]
        result = {"success": True, "message": ""}
        
        # 根据技能类型处理效果
        if skill["type"] == "investigate":
            # 调查技能：获取额外线索
            script = await self.db.get(Script, session.script_id)
            script_data = json.loads(script.content)
            available_clues = [c for c in script_data["clues"] if c not in session.discovered_clues]
            
            if available_clues:
                new_clue = available_clues[0]
                session.discovered_clues.append(new_clue)
                result["message"] = f"发现新线索：{new_clue['name']}"
            else:
                result["message"] = "没有找到新的线索"
                
        elif skill["type"] == "protect":
            # 保护技能：阻止一次投票
            if target and target in session.participants:
                session.votes.pop(target, None)
                result["message"] = f"成功保护 {target} 免受投票"
            else:
                result["success"] = False
                result["message"] = "无效的保护目标"
                
        elif skill["type"] == "expose":
            # 揭露技能：显示目标角色的某些信息
            if target and target in session.participants:
                target_index = session.participants.index(target)
                script = await self.db.get(Script, session.script_id)
                script_data = json.loads(script.content)
                target_character = script_data["characters"][target_index]
                result["message"] = f"揭露信息：{target_character['name']}的动机是{target_character['motive']}"
            else:
                result["success"] = False
                result["message"] = "无效的目标"
        
        # 标记技能为已使用
        player_state["used_skills"].add(skill_name)
        session.player_states[user] = player_state
        
        # 添加系统消息
        skill_message = {
            "sender": "system",
            "content": f"{user}使用了技能{skill_name}：{result['message']}",
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages.append(skill_message)
        
        return result

    def build_ai_context(self, session: GameSession, ai_id: str, script_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """构建AI的上下文信息"""
        context = []
        
        # 添加系统消息
        system_message = {
            "role": "system",
            "content": "你是一个剧本杀游戏中的角色，请根据你的角色设定和当前剧情发展来回应。"
        }
        context.append(system_message)
        
        # 添加角色信息
        character_index = session.participants.index(ai_id)
        if character_index < len(script_data["characters"]):
            character = script_data["characters"][character_index]
            character_info = {
                "role": "system",
                "content": f"你的角色：{character['name']}\n背景：{character['background']}\n动机：{character['motive']}"
            }
            context.append(character_info)
        
        # 添加已知线索
        clues_info = {
            "role": "system",
            "content": "已知线索：\n" + "\n".join([f"- {clue['name']}: {clue['description']}" for clue in session.discovered_clues])
        }
        context.append(clues_info)
        
        # 添加最近的对话历史
        recent_messages = session.messages[-5:] if len(session.messages) > 5 else session.messages
        for msg in recent_messages:
            context.append({
                "role": "user" if msg["sender"] != ai_id else "assistant",
                "content": f"{msg['sender']}: {msg['content']}"
            })
        
        return context

    async def end_game(self, session: GameSession):
        """结束游戏并评估获胜者"""
        # 统计投票
        vote_count = {}
        for vote_target in session.votes.values():
            vote_count[vote_target] = vote_count.get(vote_target, 0) + 1
        
        # 找出票数最多的玩家
        max_votes = max(vote_count.values())
        voted_out = [p for p, v in vote_count.items() if v == max_votes]
        
        # 获取剧本信息
        script = await self.db.get(Script, session.script_id)
        script_data = json.loads(script.content)
        murderer = next(c["name"] for c in script_data["characters"] if c.get("is_murderer", False))
        
        # 判断游戏结果
        if len(voted_out) == 1 and voted_out[0] == murderer:
            winner = "good"  # 好人阵营胜利
            result_message = "正义得到伸张！凶手被成功找出！"
        else:
            winner = "evil"  # 凶手阵营胜利
            result_message = "凶手逍遥法外..."
        
        # 更新游戏状态
        session.status = "completed"
        session.winner = winner
        
        # 添加结束消息
        end_message = {
            "sender": "system",
            "content": f"游戏结束！{result_message}\n凶手是：{murderer}",
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages.append(end_message)
        
        await self.db.commit() 