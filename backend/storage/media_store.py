"""对象存储服务（MinIO / S3）"""
from __future__ import annotations

import structlog
from pathlib import Path
from typing import Any

from backend.config import settings

logger = structlog.get_logger(__name__)


class MediaStore:
    """对象存储服务
    
    支持 MinIO 和兼容 S3 的存储后端。
    """

    def __init__(self):
        self._client = None

    async def connect(self) -> None:
        """初始化存储客户端"""
        try:
            from minio import Minio
            self._client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
            # 确保存储桶存在
            if not self._client.bucket_exists(settings.minio_bucket):
                self._client.make_bucket(settings.minio_bucket)
                logger.info("media_store.bucket_created", bucket=settings.minio_bucket)
            logger.info("media_store.connected", endpoint=settings.minio_endpoint)
        except ImportError:
            logger.warning("media_store.minio_client_not_installed")
        except Exception as e:
            logger.error("media_store.connect_failed", error=str(e))

    async def upload_file(
        self,
        file_path: Path,
        object_name: str,
        content_type: str = "application/octet-stream",
    ) -> str | None:
        """上传文件到对象存储
        
        Args:
            file_path: 本地文件路径
            object_name: 对象名称（存储路径）
            content_type: MIME 类型
            
        Returns:
            str: 对象 URL，失败返回 None
        """
        if not self._client:
            return None
        try:
            self._client.fput_object(
                settings.minio_bucket,
                object_name,
                str(file_path),
                content_type=content_type,
            )
            url = f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"
            logger.info("media_store.uploaded", object_name=object_name)
            return url
        except Exception as e:
            logger.error("media_store.upload_failed", object_name=object_name, error=str(e))
            return None

    async def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
    ) -> str | None:
        """上传字节数据到对象存储"""
        if not self._client:
            return None
        try:
            import io
            self._client.put_object(
                settings.minio_bucket,
                object_name,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            url = f"{'https' if settings.minio_secure else 'http'}://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"
            logger.info("media_store.uploaded_bytes", object_name=object_name, size=len(data))
            return url
        except Exception as e:
            logger.error("media_store.upload_bytes_failed", object_name=object_name, error=str(e))
            return None

    async def download_file(
        self,
        object_name: str,
        dest_path: Path,
    ) -> Path | None:
        """下载文件到本地"""
        if not self._client:
            return None
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            self._client.fget_object(
                settings.minio_bucket,
                object_name,
                str(dest_path),
            )
            logger.info("media_store.downloaded", object_name=object_name)
            return dest_path
        except Exception as e:
            logger.error("media_store.download_failed", object_name=object_name, error=str(e))
            return None

    async def delete_file(self, object_name: str) -> bool:
        """删除文件"""
        if not self._client:
            return False
        try:
            self._client.remove_object(settings.minio_bucket, object_name)
            logger.info("media_store.deleted", object_name=object_name)
            return True
        except Exception as e:
            logger.error("media_store.delete_failed", object_name=object_name, error=str(e))
            return False

    async def get_presigned_url(
        self,
        object_name: str,
        expires: int = 3600,
    ) -> str | None:
        """获取预签名 URL（临时访问链接）"""
        if not self._client:
            return None
        try:
            from datetime import timedelta
            url = self._client.presigned_get_object(
                settings.minio_bucket,
                object_name,
                expires=timedelta(seconds=expires),
            )
            return url
        except Exception as e:
            logger.error("media_store.presign_failed", object_name=object_name, error=str(e))
            return None


# 全局单例
media_store = MediaStore()
