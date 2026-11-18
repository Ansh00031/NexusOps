import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.agents.orchestrator import ws_manager

logger = logging.getLogger("nexusops.websocket")
router = APIRouter(tags=["websocket"])

@router.websocket("/ws/incidents/{incident_id}")
async def websocket_incident_endpoint(websocket: WebSocket, incident_id: str):
    await websocket.accept()
    ws_manager.register(incident_id, websocket)
    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "incident_id": incident_id,
            "message": "Connected to live NexusOps reasoning stream"
        })
        while True:
            # Keep connection alive; accept any client messages/pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.unregister(incident_id, websocket)
    except Exception as e:
        logger.debug(f"WebSocket closed: {e}")
        ws_manager.unregister(incident_id, websocket)
