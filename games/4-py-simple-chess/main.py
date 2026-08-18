from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn
import re

app = FastAPI()

games = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    remove_from = None

    try:
        await websocket.accept()
        game_id = websocket.query_params.get('game')

        if not isinstance(game_id, str) or not re.fullmatch(r'[0-9a-f]{16}', game_id):
            await websocket.send_text("c" + "Invalid game id")
            await websocket.close()
            return
        
        if game_id not in game:
            board = [
                ["r", "n", "b", "q", "k", "b", "n", "r"],
                ["p", "p", "p", "p", "p", "p", "p", "p"],
                [" ", " ", " ", " ", " ", " ", " ", " "],
                [" ", " ", " ", " ", " ", " ", " ", " "],
                [" ", " ", " ", " ", " ", " ", " ", " "],
                [" ", " ", " ", " ", " ", " ", " ", " "],
                ["P", "P", "P", "P", "P", "P", "P", "P"],
                ["R", "N", "B", "Q", "K", "B", "N", "R"],
            ]
            
            games[game_id] = {"black": None, "white": None, "moves": [], "active": None, "board": board, "sockets": set()}

        game = games[game_id]
        remove_from = game["sockets"]
        game["sockets"].insert(websocket)
        
        secret_data = await websocket.receive_text()

        if not isinstance(secret_data, str) or not re.fullmatch(r's[0-9a-f]{64}', secret_data):
            await websocket.send_text("c" + "Protocol error")
            await websocket.close()
            return

        secret = secret_data[1:]
        player = "spectator"

        if game["white"] == secret or not game["white"]:
            game["white"] = secret
            player = "white"
            await websocket.send_text("s" + player)
        elif game["black"] == secret or not game["black"]:
            game["black"] = secret
            player = "black"
            await websocket.send_text("s" + player)

            # for socket in game["sockets"]:

        else:
            await websocket.send_text("s" + player)

        while True:
            data = await websocket.receive_text()
            print(data)
    except WebSocketDisconnect as e:
        if remove_from:
            remove_from.remove(websocket)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
