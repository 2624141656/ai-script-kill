from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    role = Column(String, default="user")  # 用户角色：user, admin
    avatar_url = Column(String, nullable=True)  # 头像URL
    bio = Column(String, nullable=True)  # 用户简介

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "role": self.role,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class Script(Base):
    __tablename__ = "scripts"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    category = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ai_count = Column(Integer, default=0)
    is_user_uploaded = Column(Boolean, default=False)

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(String, primary_key=True)
    script_id = Column(String, ForeignKey("scripts.id"))
    participants = Column(JSON)  # 存储参与者列表
    messages = Column(JSON)  # 存储消息历史
    private_messages = Column(JSON, default=[])  # 私聊消息
    discovered_clues = Column(JSON, default=[])  # 已发现的线索
    phase = Column(String, default="preparation")  # 游戏阶段：preparation, discussion, voting, result
    round_number = Column(Integer, default=0)  # 当前回合数
    votes = Column(JSON, default={})  # 投票结果
    current_speaker = Column(String, nullable=True)  # 当前发言者
    player_states = Column(JSON, default={})  # 玩家状态（包括技能使用情况等）
    status = Column(String, default="active")
    winner = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIPlatform(Base):
    __tablename__ = "ai_platforms"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    api_endpoint = Column(String, nullable=False)
    model = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow) 