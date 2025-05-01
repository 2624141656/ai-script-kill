import os
import uuid
from fastapi import UploadFile, HTTPException
from typing import Optional
import aiofiles
from datetime import datetime

class FileHandler:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self.max_file_size = 1024 * 1024  # 1MB
        self.allowed_extensions = {".txt", ".doc", ".docx", ".pdf"}
        
        # 确保上传目录存在
        os.makedirs(upload_dir, exist_ok=True)

    async def save_upload_file(self, file: UploadFile) -> str:
        """保存上传的文件并返回文件路径"""
        # 检查文件大小
        file_size = 0
        chunk_size = 1024
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if file_size > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件大小超过限制（{self.max_file_size/1024/1024}MB）"
                )
        await file.seek(0)
        
        # 检查文件扩展名
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。允许的类型：{', '.join(self.allowed_extensions)}"
            )
        
        # 生成唯一的文件名
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        return file_path

    async def read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
                return content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"读取文件失败：{str(e)}"
            )

    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return {
            "filename": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "created_at": datetime.fromtimestamp(os.path.getctime(file_path)),
            "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path))
        }

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"删除文件失败：{str(e)}"
            ) 