import logging

import socketio
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.BACKEND_CORS_ORIGINS or "*",
)


def _org_room(organization_id: str) -> str:
    return f"org:{organization_id}"


@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    if not token:
        raise ConnectionRefusedError("Missing authentication token")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise ConnectionRefusedError("Invalid authentication token")

    org_id = payload.get("org_id")
    if not org_id:
        raise ConnectionRefusedError("Token missing organization scope")

    await sio.save_session(sid, {"organization_id": org_id, "user_id": payload.get("sub")})
    await sio.enter_room(sid, _org_room(org_id))
    logger.info(f"Socket connected: sid={sid} org={org_id}")


@sio.event
async def disconnect(sid):
    logger.info(f"Socket disconnected: sid={sid}")


async def emit_to_organization(organization_id: str, event: str, data: dict) -> None:
    await sio.emit(event, data, room=_org_room(organization_id))
