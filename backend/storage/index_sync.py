"""Elasticsearch 索引同步"""
from __future__ import annotations

import structlog
from datetime import datetime, UTC
from typing import Any

logger = structlog.get_logger(__name__)


class IndexSync:
    """Elasticsearch 索引同步服务
    
    将标准化数据同步到 Elasticsearch 以支持全文检索。
    """

    def __init__(self):
        self._client = None

    async def connect(self, url: str = "http://localhost:9200") -> None:
        """连接 Elasticsearch"""
        try:
            from elasticsearch import AsyncElasticsearch
            self._client = AsyncElasticsearch(url)
            logger.info("elasticsearch.connected", url=url)
        except ImportError:
            logger.warning("elasticsearch.client_not_installed")
        except Exception as e:
            logger.error("elasticsearch.connect_failed", error=str(e))

    async def disconnect(self) -> None:
        """断开连接"""
        if self._client:
            await self._client.close()
            logger.info("elasticsearch.disconnected")

    async def ensure_index(self, index_name: str, mapping: dict[str, Any]) -> None:
        """确保索引存在，不存在则创建"""
        if not self._client:
            return
        try:
            exists = await self._client.indices.exists(index=index_name)
            if not exists:
                await self._client.indices.create(index=index_name, body=mapping)
                logger.info("elasticsearch.index_created", index=index_name)
        except Exception as e:
            logger.error("elasticsearch.ensure_index_failed", index=index_name, error=str(e))

    async def index_document(
        self,
        index_name: str,
        doc_id: str,
        document: dict[str, Any],
    ) -> bool:
        """索引单个文档"""
        if not self._client:
            return False
        try:
            await self._client.index(
                index=index_name,
                id=doc_id,
                document=document,
            )
            return True
        except Exception as e:
            logger.error(
                "elasticsearch.index_failed",
                index=index_name,
                doc_id=doc_id,
                error=str(e),
            )
            return False

    async def bulk_index(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        id_field: str = "id",
    ) -> int:
        """批量索引文档"""
        if not self._client or not documents:
            return 0
        try:
            actions = []
            for doc in documents:
                actions.append({"index": {"_index": index_name, "_id": doc.get(id_field)}})
                actions.append(doc)

            response = await self._client.bulk(operations=actions)
            errors = response.get("errors", False)
            if errors:
                logger.warning("elasticsearch.bulk_partial_failure", index=index_name)
            return len(documents)
        except Exception as e:
            logger.error("elasticsearch.bulk_failed", index=index_name, error=str(e))
            return 0

    async def search(
        self,
        index_name: str,
        query: dict[str, Any],
        size: int = 20,
    ) -> list[dict[str, Any]]:
        """搜索文档"""
        if not self._client:
            return []
        try:
            response = await self._client.search(
                index=index_name,
                query=query,
                size=size,
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logger.error("elasticsearch.search_failed", index=index_name, error=str(e))
            return []


# 全局单例
index_sync = IndexSync()
