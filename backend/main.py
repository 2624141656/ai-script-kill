from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime, timedelta
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from models import Script, GameSession, AIPlatform, User
from database import get_db, init_db
from ai_service import AIService
from game_logic import GameManager
from file_handler import FileHandler
from auth import (
    create_access_token,
    get_current_active_user,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
ai_service = AIService()
game_manager = None
file_handler = FileHandler()

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 数据模型
class ScriptCreate(BaseModel):
    title: str
    content: str
    category: str
    is_user_uploaded: bool = False

class GameSessionCreate(BaseModel):
    script_id: str
    ai_count: int
    is_all_ai: bool = False

class MessageCreate(BaseModel):
    content: str
    sender: str

# 用户相关模型
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    role: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: str
    last_login: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    await init_db()
    global game_manager
    game_manager = GameManager(await get_db().__anext__(), ai_service)

@app.post("/scripts/generate")
async def generate_scripts(
    category: str,
    count: int = 5,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    generated_scripts = []
    for i in range(count):
        script_data = await ai_service.generate_script(category)
        script = Script(
            id=str(uuid.uuid4()),
            title=script_data["title"],
            content=json.dumps(script_data, ensure_ascii=False),
            category=category,
            created_at=datetime.utcnow(),
            ai_count=0,
            is_user_uploaded=False
        )
        db.add(script)
        generated_scripts.append(script)
    await db.commit()
    return generated_scripts

@app.post("/scripts/upload")
async def upload_script(
    file: UploadFile = File(None),
    content: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if file:
        # 处理文件上传
        file_path = await file_handler.save_upload_file(file)
        content = await file_handler.read_file_content(file_path)
        
        new_script = Script(
            id=str(uuid.uuid4()),
            title=file.filename,
            content=content,
            category="user_uploaded",
            created_at=datetime.utcnow(),
            ai_count=0,
            is_user_uploaded=True
        )
    elif content:
        # 处理文本输入
        new_script = Script(
            id=str(uuid.uuid4()),
            title="User Uploaded Script",
            content=content,
            category="user_uploaded",
            created_at=datetime.utcnow(),
            ai_count=0,
            is_user_uploaded=True
        )
    else:
        raise HTTPException(status_code=400, detail="必须提供文件或文本内容")
    
    db.add(new_script)
    await db.commit()
    return new_script

@app.post("/game/start")
async def start_game(
    game_data: GameSessionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    script = await db.get(Script, game_data.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    session = GameSession(
        id=str(uuid.uuid4()),
        script_id=game_data.script_id,
        participants=[],
        messages=[],
        status="active"
    )
    
    # 添加AI参与者
    if game_data.is_all_ai or game_data.ai_count > 0:
        ai_count = game_data.ai_count if not game_data.is_all_ai else 5  # 默认5个AI
        for i in range(ai_count):
            session.participants.append(f"ai_{i}")
    
    db.add(session)
    await db.commit()
    
    # 启动游戏流程
    background_tasks.add_task(game_manager.run_game_session, session.id)
    
    return session

@app.post("/game/{session_id}/message")
async def send_message(
    session_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    new_message = {
        "sender": message.sender,
        "content": message.content,
        "timestamp": datetime.utcnow().isoformat()
    }
    session.messages.append(new_message)
    await db.commit()
    
    # 如果是AI的消息，生成响应
    if message.sender.startswith("ai_"):
        response = await ai_service.generate_response(
            session_id,
            message.content,
            context=session.messages[-5:]  # 使用最近5条消息作为上下文
        )
        ai_message = {
            "sender": message.sender,
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages.append(ai_message)
        await db.commit()
    
    return session

@app.get("/game/{session_id}")
async def get_game_status(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    return session

# 用户认证路由
@app.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    result = await db.execute(select(User).filter(User.username == user.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 检查邮箱是否已存在
    result = await db.execute(select(User).filter(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建新用户
    db_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        hashed_password=User.get_password_hash(user.password),
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user.to_dict()

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# 用户管理路由
@app.get("/users/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user.to_dict()

@app.put("/users/me", response_model=dict)
async def update_user(
    bio: str = None,
    avatar_url: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新当前用户信息"""
    if bio is not None:
        current_user.bio = bio
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    
    await db.commit()
    return current_user.to_dict()

@app.post("/users/me/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    if not current_user.verify_password(old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    current_user.hashed_password = User.get_password_hash(new_password)
    await db.commit()
    return {"message": "Password updated successfully"}

# 游戏相关路由
@app.post("/game/{session_id}/private-message")
async def send_private_message(
    session_id: str,
    receiver: str,
    content: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """发送私聊消息"""
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if receiver not in session.participants:
        raise HTTPException(status_code=400, detail="Receiver not in game")
    
    private_message = {
        "sender": current_user.username,
        "receiver": receiver,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    session.private_messages.append(private_message)
    await db.commit()
    return {"message": "Private message sent"}

@app.post("/game/{session_id}/discover-clue")
async def discover_clue(
    session_id: str,
    clue_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """发现线索"""
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    script = await db.get(Script, session.script_id)
    script_data = json.loads(script.content)
    
    # 检查线索是否存在
    clue = next((c for c in script_data["clues"] if c["id"] == clue_id), None)
    if not clue:
        raise HTTPException(status_code=404, detail="Clue not found")
    
    # 添加到已发现线索列表
    if clue not in session.discovered_clues:
        session.discovered_clues.append(clue)
        # 广播线索发现消息
        system_message = {
            "sender": "system",
            "content": f"{current_user.username} 发现了线索：{clue['name']}",
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages.append(system_message)
    
    await db.commit()
    return {"message": "Clue discovered"}

@app.post("/game/{session_id}/vote")
async def submit_vote(
    session_id: str,
    target: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """提交投票"""
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if session.phase != "voting":
        raise HTTPException(status_code=400, detail="Not in voting phase")
    
    if target not in session.participants:
        raise HTTPException(status_code=400, detail="Invalid vote target")
    
    # 记录投票
    session.votes[current_user.username] = target
    
    # 检查是否所有人都已投票
    if len(session.votes) == len(session.participants):
        # 计算投票结果
        vote_count = {}
        for vote_target in session.votes.values():
            vote_count[vote_target] = vote_count.get(vote_target, 0) + 1
        
        # 找出票数最多的玩家
        max_votes = max(vote_count.values())
        voted_out = [p for p, v in vote_count.items() if v == max_votes]
        
        # 处理投票结果
        result_message = {
            "sender": "system",
            "content": f"投票结果：{'平票' if len(voted_out) > 1 else f'{voted_out[0]}被投票出局'}",
            "timestamp": datetime.utcnow().isoformat()
        }
        session.messages.append(result_message)
        
        # 进入结果阶段
        session.phase = "result"
    
    await db.commit()
    return {"message": "Vote submitted"}

@app.post("/game/{session_id}/next-phase")
async def advance_game_phase(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """推进游戏阶段"""
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    # 定义阶段顺序
    phases = ["preparation", "discussion", "voting", "result"]
    current_index = phases.index(session.phase)
    next_phase = phases[(current_index + 1) % len(phases)]
    
    # 处理阶段转换
    if next_phase == "discussion":
        session.round_number += 1
        # 重置发言顺序
        session.current_speaker = session.participants[0]
    elif next_phase == "voting":
        session.votes = {}  # 清空投票
    elif next_phase == "result":
        # 检查游戏是否结束
        if await game_manager.check_game_end_conditions(session, None):
            session.status = "completed"
    elif next_phase == "preparation":
        # 新的回合开始
        pass
    
    session.phase = next_phase
    
    # 添加阶段变更消息
    phase_message = {
        "sender": "system",
        "content": f"游戏进入{next_phase}阶段",
        "timestamp": datetime.utcnow().isoformat()
    }
    session.messages.append(phase_message)
    
    await db.commit()
    return {"message": f"Advanced to {next_phase} phase"}

@app.post("/game/{session_id}/use-skill")
async def use_character_skill(
    session_id: str,
    skill_name: str,
    target: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """使用角色技能"""
    session = await db.get(GameSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    # 获取玩家的角色信息
    script = await db.get(Script, session.script_id)
    script_data = json.loads(script.content)
    player_index = session.participants.index(current_user.username)
    character = script_data["characters"][player_index]
    
    # 检查技能是否可用
    if skill_name not in character.get("skills", {}):
        raise HTTPException(status_code=400, detail="Skill not available")
    
    # 检查技能是否已使用
    player_state = session.player_states.get(current_user.username, {})
    if player_state.get(f"used_skill_{skill_name}", False):
        raise HTTPException(status_code=400, detail="Skill already used")
    
    # 使用技能
    skill_result = await game_manager.handle_skill_use(
        session,
        current_user.username,
        skill_name,
        target
    )
    
    # 标记技能为已使用
    if current_user.username not in session.player_states:
        session.player_states[current_user.username] = {}
    session.player_states[current_user.username][f"used_skill_{skill_name}"] = True
    
    await db.commit()
    return skill_result

@app.get("/scripts")
async def get_scripts(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Script)
    if category:
        query = query.filter(Script.category == category)
    result = await db.execute(query)
    scripts = result.scalars().all()
    return scripts

@app.get("/scripts/{script_id}")
async def get_script(
    script_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@app.post("/scripts/decrypt")
async def decrypt_script(
    script_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # 调用AI服务解密剧本
    decrypted_content = await ai_service.decrypt_script(script.content)
    
    return {
        "id": script.id,
        "title": script.title,
        "content": decrypted_content,
        "category": script.category
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 