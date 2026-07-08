import logging
from qdrant_client.http.models import Distance, VectorParams
from app.core.database import get_qdrant_client, verify_qdrant
from app.core.config import settings
import httpx

logger = logging.getLogger(__name__)

COLLECTION_NAME = "kb_articles"
VECTOR_DIMENSION = 1536

async def get_embedding(text: str) -> list[float]:
    """Generates embedding vector from OpenAI API if available, otherwise deterministic hash vector."""
    if settings.OPENAI_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": text,
                        "model": "text-embedding-3-small"
                    },
                    timeout=5.0
                )
                if res.status_code == 200:
                    return res.json()["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"OpenAI embeddings call failed: {e}")
            
    h = hash(text)
    return [((h + idx) % 1000) / 1000.0 for idx in range(VECTOR_DIMENSION)]


def init_qdrant_collection():
    """Initializes Qdrant kb_articles collection on app startup."""
    try:
        client = get_qdrant_client()
        collections = client.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        if not exists:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_DIMENSION, distance=Distance.COSINE),
            )
            logger.info(f"Qdrant collection {COLLECTION_NAME} created successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize Qdrant collection: {e}")


async def upsert_kb_article_vector(article_id: str, title: str, category: str):
    """Generates embeddings and upserts into Qdrant index."""
    try:
        if not await verify_qdrant():
            return
            
        vector = await get_embedding(f"{title} - {category}")
        client = get_qdrant_client()
        
        import uuid
        try:
            point_id = int(uuid.UUID(article_id).int & 0xffffffffffffffff)
        except Exception:
            point_id = abs(hash(article_id)) % (10 ** 10)
            
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": point_id,
                "vector": vector,
                "payload": {"id": article_id, "title": title, "category": category}
            }]
        )
    except Exception as e:
        logger.error(f"Failed to upsert vector in Qdrant: {e}")
