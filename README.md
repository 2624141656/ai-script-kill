# 剧本杀 AI 助手

一个基于 AI 的剧本杀游戏助手应用。

## 功能特点

- 用户注册和登录
- AI 剧本生成
- 多人游戏支持
- 实时对话系统
- 角色扮演辅助

## 技术栈

- 后端：FastAPI + SQLite
- 前端：Vue.js + Element Plus
- 移动端：Kivy
- AI：OpenAI API

## 开发环境设置

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/script-kill.git
cd script-kill
```

2. 安装后端依赖：
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖：
```bash
cd frontend
npm install
```

4. 启动后端服务：
```bash
cd backend
uvicorn main:app --reload
```

5. 启动前端服务：
```bash
cd frontend
npm run dev
```

## 构建 Android APK

项目使用 GitHub Actions 自动构建 Android APK。每次推送到 main 分支时，都会自动构建新的 APK。

## 许可证

MIT

## 项目结构

```
.
├── backend/            # Python FastAPI后端
│   ├── main.py        # 主应用文件
│   └── requirements.txt # 依赖文件
├── frontend/          # Vue3前端
│   ├── src/          # 源代码
│   ├── public/       # 静态资源
│   └── package.json  # 前端依赖
└── README.md         # 项目文档
```

## 打包指南

### 打包为Windows应用

1. 使用PyInstaller打包后端：
```