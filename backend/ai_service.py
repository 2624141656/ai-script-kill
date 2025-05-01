from typing import List, Dict, Any
import json
from ai_platforms import AIPlatformManager

class AIService:
    def __init__(self):
        self.platform_manager = AIPlatformManager()
        self.default_platform = "openai"

    async def generate_script(self, category: str, platform: str = None) -> Dict[str, Any]:
        """生成剧本"""
        platform = platform or self.default_platform
        prompt = f"""
        请生成一个{category}类型的剧本杀剧本。要求：
        1. 包含完整的故事背景
        2. 包含3-5个角色
        3. 每个角色有详细的背景故事和动机
        4. 包含关键线索和证据
        5. 包含结局和真相
        请以JSON格式返回，包含以下字段：
        - title: 剧本标题
        - background: 故事背景
        - characters: 角色列表，每个角色包含name, background, motive
        - clues: 关键线索列表
        - ending: 结局和真相
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的剧本杀编剧。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.platform_manager.generate_response(platform, messages)
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果返回的不是有效的JSON，返回一个默认结构
            return {
                "title": f"{category}剧本",
                "background": "默认背景故事",
                "characters": [],
                "clues": [],
                "ending": "默认结局"
            }

    async def generate_response(self, 
                             session_id: str,
                             message: str,
                             platform: str = None,
                             context: List[Dict[str, str]] = None) -> str:
        """生成AI响应"""
        platform = platform or self.default_platform
        if context is None:
            context = []
            
        messages = [
            {"role": "system", "content": "你是一个剧本杀游戏中的角色，请根据你的角色设定和当前剧情发展来回应。"},
            *context,
            {"role": "user", "content": message}
        ]
        
        return await self.platform_manager.generate_response(platform, messages)

    async def evaluate_winner(self, 
                            session_id: str,
                            messages: List[Dict[str, str]],
                            platform: str = None) -> str:
        """评估游戏获胜者"""
        platform = platform or self.default_platform
        prompt = """
        请根据以下对话历史，评估谁是最终的获胜者。
        评估标准：
        1. 角色扮演的准确性
        2. 推理的合理性
        3. 对剧情的贡献度
        4. 互动质量
        请返回获胜者的ID。
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的剧本杀裁判。"},
            {"role": "user", "content": prompt + "\n对话历史：\n" + json.dumps(messages, ensure_ascii=False)}
        ]
        
        return await self.platform_manager.generate_response(platform, messages, temperature=0.3)

    async def decrypt_script(self, encrypted_content: str, platform: str = None) -> Dict[str, Any]:
        """解密剧本内容"""
        platform = platform or self.default_platform
        prompt = f"""
        请解密以下剧本内容，并保持原有的JSON格式：
        {encrypted_content}
        
        要求：
        1. 保持原有的JSON结构
        2. 解密所有加密的文本内容
        3. 确保解密后的内容符合剧本格式
        """
        
        messages = [
            {"role": "system", "content": "你是一个专业的剧本解密专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.platform_manager.generate_response(platform, messages)
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果解密失败，返回原始内容
            return encrypted_content 