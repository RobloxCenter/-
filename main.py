import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATA_FILE = "counter.txt"
GOAL = 820000

def load_counter():
    if not os.path.exists(DATA_FILE):
        return 0
    with open(DATA_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except ValueError:
            return 0

def save_counter(value):
    with open(DATA_FILE, "w") as f:
        f.write(str(value))

global_counter = load_counter()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global global_counter
    await manager.connect(websocket)
    await websocket.send_text(str(global_counter))

    try:
        while True:
            data = await websocket.receive_text()
            if global_counter < GOAL:
                if data == "click":
                    global_counter += 1
                    save_counter(global_counter)
                    await manager.broadcast(str(global_counter))
            else:
                await manager.broadcast(str(global_counter))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
