from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import HTMLResponse
import os
import uvicorn

app = FastAPI()

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod cambiar por tu dominio
    allow_methods=["*"],
    allow_headers=["*"]
)

# Modelo de login
class LoginData(BaseModel):
    user: str
    password: str

# URL de PostgreSQL en Railway
DATABASE_URL = "postgresql://postgres:HlfvHoCcqVIrpUOHzoHkYTDVlsxfdUSu@nozomi.proxy.rlwy.net:24651/railway"

# Conexión a la DB
async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

# Monta frontend como /static (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Función genérica para servir HTML con UTF-8
def serve_html(filename: str):
    path = Path("frontend") / filename
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="Archivo no encontrado", status_code=404)

# Endpoints para HTML
@app.get("/", response_class=HTMLResponse)
async def root():
    return serve_html("index.html")

@app.get("/app.html", response_class=HTMLResponse)
async def app_page():
    return serve_html("app.html")

# Login simple (texto plano)
@app.post("/login")
async def login(data: LoginData):
    conn = await get_connection()
    try:
        user = await conn.fetchrow("SELECT * FROM usuarios WHERE id=$1", data.user)
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        if data.password != user['password']:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        return {"message": "Login correcto"}
    finally:
        await conn.close()

# Puerto dinámico para Railway
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

