from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import HTMLResponse

app = FastAPI()

# Configuración
app = FastAPI()

# CORS para tu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambiar por tu dominio real en prod
    allow_methods=["*"],
    allow_headers=["*"]
)

# Modelo de login
class LoginData(BaseModel):
    user: str
    password: str

# URL de Railway (asyncpg)
DATABASE_URL = "postgresql://postgres:HlfvHoCcqVIrpUOHzoHkYTDVlsxfdUSu@nozomi.proxy.rlwy.net:24651/railway"
                
# Función para obtener conexión
async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

# Monta toda la carpeta frontend como estática
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Función genérica para servir HTML con UTF-8
def serve_html(filename: str):
    path = Path("frontend") / filename
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="Archivo no encontrado", status_code=404)

# Página raíz
@app.get("/", response_class=HTMLResponse)
async def root():
    return serve_html("index.html")


@app.get("/app.html", response_class=HTMLResponse)
async def app_page():
    path = Path("frontend") / "app.html"  # <- aquí está dentro de frontend
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="Archivo no encontrado", status_code=404)


@app.post("/login")
async def login(data: LoginData):
    
    conn = await get_connection()
    try:
        user = await conn.fetchrow("SELECT * FROM usuarios WHERE id=$1", data.user)
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        # Comparación directa (texto plano)
        if data.password != user['password']:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        return {"message": "Login correcto"}
    finally:
        await conn.close()


