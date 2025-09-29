from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import HTMLResponse
import os
import uvicorn
import logging

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

# URL de PostgreSQL en Railway desde variable de entorno
DATABASE_URL = 'postgresql://postgres:kEHmlYsNdNfQAHngoJfGyYDXJXSJiWaw@shortline.proxy.rlwy.net:40143/railway'
#DATABASE_URL = os.environ.get("DATABASE_URL")

# Conexión a la DB
async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

# Monta frontend como /static (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="frontend"), name="static")
# Opcional: monta /assets para compatibilidad con rutas antiguas
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
# Monta vistas HTML parciales
app.mount("/views", StaticFiles(directory="frontend/views"), name="views")


# Función genérica para servir HTML con UTF-8
def serve_html(filename: str):
    path = Path("frontend") / filename
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="Archivo no encontrado", status_code=404)

# Endpoint para login.html
@app.get("/index.html", response_class=HTMLResponse)
async def index_page():
    return serve_html("index.html")

# Endpoints para HTML
@app.get("/", response_class=HTMLResponse)
async def root():
    return serve_html("index.html")

@app.get("/app.html", response_class=HTMLResponse)
async def app_page():
    return serve_html("app.html")


# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Login simple (texto plano) con logging
@app.post("/login")
async def login(data: LoginData):
    conn = await get_connection()
    logger.info(f"Datos recibidos del login: {data}")
    try:
        # Listar tablas disponibles
        tablas = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables
            WHERE table_schema='public'
        """)
        logger.info("Tablas disponibles en la DB:")
        for t in tablas:
            logger.info(f"- {t['table_name']}")
        
        # Consulta de usuario
        query = "SELECT * FROM usuarios WHERE id=$1"
        logger.info(f"Ejecutando query: {query} con id = {data.user}")
        user = await conn.fetchrow(query, data.user)
        
        if not user:
            logger.warning(f"Usuario no encontrado: {data.user}")
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        if data.password != user['password']:
            logger.warning(f"Contraseña incorrecta para usuario: {data.user}")
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        
        logger.info(f"Login correcto para usuario: {data.user}")
        return {"message": "Login correcto"}
    finally:
        await conn.close()



# Puerto dinámico para Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
