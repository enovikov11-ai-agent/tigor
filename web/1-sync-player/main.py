from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
import os

root_path = os.getenv("ROOT_PATH", "")

app = FastAPI(root_path=root_path)

videos = os.listdir("./videos")

global clients
global state

clients = set()
state = {
    'sessionId': 0,
    'selected': videos[0] if videos else '',
    'canPlay': set()
}

async def broadcast(message):
    for client in clients:
        try:
            await client.send_json(message)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(e)

app.mount("/videos", StaticFiles(directory="videos"), name="videos")

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    global state
    global clients

    try:
        await websocket.accept()
        clients.add(websocket)

        currentSessionId = state['sessionId']
        await websocket.send_json({"sessionId": currentSessionId, 'selected': state['selected']})
        state['sessionId'] += 1

        await broadcast({"videos": os.listdir("./videos")})

        while True:
            message = await websocket.receive_json()

            if "selected" in message:
                state['selected'] = message['selected']
                state['canPlay'] = set()
                await broadcast({"selected": state['selected']})
            
            if "canPlay" in message:
                state['canPlay'].add(currentSessionId)
                await broadcast({"canPlay": list(state['canPlay'])})
            
            if "play" in message:
                await broadcast({"play": message["play"]})

            print(message)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(e)
    finally:
        clients.remove(websocket)
        state['canPlay'].remove(currentSessionId)

        await broadcast({"canPlay": list(state['canPlay'])})

@app.get("/")
async def index():
    return FileResponse("index.html")
