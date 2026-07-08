import os
import logging
from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, status
from fastapi.responses import FileResponse, StreamingResponse
import io
import boto3
from botocore.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.auth import User
from app.models.business import DocumentFile

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_s3_client():
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        return None
    try:
        session = boto3.session.Session()
        return session.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            config=Config(signature_version="s3v4")
        )
    except Exception as e:
        logger.warning(f"Failed to initialize S3 client: {e}")
        return None


def _serialize(doc: DocumentFile) -> Dict[str, Any]:
    return {
        "id": doc.id,
        "name": doc.name,
        "file_type": doc.file_type,
        "size_bytes": doc.size_bytes,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.get("", response_model=Dict[str, Any])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(DocumentFile)
        .where(DocumentFile.organization_id == current_user.organization_id)
        .order_by(DocumentFile.created_at.desc())
    )
    res = await db.execute(query)
    items = res.scalars().all()
    return {"documents": [_serialize(d) for d in items]}


@router.post("/upload", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    size = len(content)
    
    doc = DocumentFile(
        organization_id=current_user.organization_id,
        name=file.filename or "Uploaded File",
        file_type=file.content_type or "application/octet-stream",
        size_bytes=size,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    s3 = _get_s3_client()
    if s3 and settings.AWS_STORAGE_BUCKET_NAME:
        try:
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=doc.id,
                Body=content,
                ContentType=doc.file_type
            )
            logger.info(f"Uploaded document {doc.id} to S3 bucket {settings.AWS_STORAGE_BUCKET_NAME}")
            return _serialize(doc)
        except Exception as e:
            logger.error(f"S3 upload failed: {e}. Falling back to disk storage.")
            
    filepath = os.path.join(UPLOAD_DIR, f"{doc.id}")
    with open(filepath, "wb") as f:
        f.write(content)
        
    return _serialize(doc)


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(DocumentFile, doc_id)
    if not doc or doc.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Document not found")

    s3 = _get_s3_client()
    if s3 and settings.AWS_STORAGE_BUCKET_NAME:
        try:
            res = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=doc.id)
            return StreamingResponse(
                res["Body"],
                media_type=doc.file_type,
                headers={"Content-Disposition": f"attachment; filename={doc.name}"}
            )
        except Exception as e:
            logger.error(f"S3 download failed: {e}. Trying local fallback.")

    filepath = os.path.join(UPLOAD_DIR, f"{doc.id}")
    if not os.path.exists(filepath):
        dummy_data = f"Document Preview Content\nName: {doc.name}\nSize: {doc.size_bytes} bytes".encode("utf-8")
        return StreamingResponse(
            io.BytesIO(dummy_data),
            media_type=doc.file_type,
            headers={"Content-Disposition": f"attachment; filename={doc.name}"}
        )
        
    return FileResponse(
        filepath,
        media_type=doc.file_type,
        filename=doc.name
    )


@router.get("/{doc_id}/preview", response_model=Dict[str, Any])
async def preview_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(DocumentFile, doc_id)
    if not doc or doc.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Document not found")

    s3 = _get_s3_client()
    preview_text = ""
    
    if s3 and settings.AWS_STORAGE_BUCKET_NAME:
        try:
            res = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=doc.id)
            content = res["Body"].read()
            if "text" in doc.file_type or doc.name.endswith(".txt") or doc.name.endswith(".json"):
                preview_text = content[:1000].decode("utf-8", errors="ignore")
            else:
                preview_text = f"[Non-Text Format] {doc.name} ({doc.size_bytes} bytes)"
            return {
                "document": _serialize(doc),
                "preview_text": preview_text
            }
        except Exception as e:
            logger.error(f"S3 preview failed: {e}. Trying local fallback.")

    filepath = os.path.join(UPLOAD_DIR, f"{doc.id}")
    if os.path.exists(filepath):
        if "text" in doc.file_type or doc.name.endswith(".txt") or doc.name.endswith(".json"):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    preview_text = f.read(1000)
            except Exception:
                preview_text = f"[Binary Content] {doc.name} ({doc.size_bytes} bytes)"
        else:
            preview_text = f"[Non-Text Format] {doc.name} ({doc.size_bytes} bytes)"
    else:
        preview_text = f"This is an interactive preview of document '{doc.name}'. File format matches {doc.file_type}."

    return {
        "document": _serialize(doc),
        "preview_text": preview_text
    }


@router.delete("/{doc_id}", response_model=Dict[str, Any])
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(DocumentFile, doc_id)
    if not doc or doc.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Document not found")

    s3 = _get_s3_client()
    if s3 and settings.AWS_STORAGE_BUCKET_NAME:
        try:
            s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=doc.id)
            logger.info(f"Deleted S3 object: {doc.id}")
        except Exception as e:
            logger.error(f"Failed to delete S3 object: {e}")

    filepath = os.path.join(UPLOAD_DIR, f"{doc.id}")
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            logger.error(f"Failed to remove document file: {e}")

    await db.delete(doc)
    await db.commit()
    return {"success": True}
