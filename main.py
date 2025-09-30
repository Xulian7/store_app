from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from pathlib import Path
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

# -------------------------------
# MODELOS
# -------------------------------
class LoginData(BaseModel):
    user: str
    password: str

class Producto(BaseModel):
    nombre: str
    referencia: str
    precio_compra: float

# -------------------------------
# CONEXIÓN A DB
# -------------------------------
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:kEHmlYsNdNfQAHngoJfGyYDXJXSJiWaw@shortline.proxy.rlwy.net:40143/railway"  # fallback local
)

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

# -------------------------------
# STATIC & VIEWS
# -------------------------------
# Carpeta de assets (CSS, JS, imágenes, etc.)
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
# Carpeta de frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# -------------------------------
# ENDPOINTS VISTAS
# -------------------------------
@app.get("/")
async def index():
    return FileResponse("frontend/index.html")

@app.get("/almacen-gestion")
async def almacen_gestion():
    return FileResponse("frontend/almacen-gestion.html")

@app.get("/clientes-gestion")
async def clientes_gestion():
    return FileResponse("frontend/clientes-gestion.html")

@app.get("/vehiculos-gestion")
async def vehiculos_gestion():
    return FileResponse("frontend/vehiculos-gestion.html")


def serve_html(filename: str):
    path = Path("frontend") / filename
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="Archivo no encontrado", status_code=404)

@app.get("/index.html", response_class=HTMLResponse)
async def index_page():
    return serve_html("index.html")

@app.get("/", response_class=HTMLResponse)
async def root():
    return serve_html("index.html")

@app.get("/app.html", response_class=HTMLResponse)
async def app_page():
    return serve_html("app.html")

# -------------------------------
# LOGGING
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# ENDPOINT LOGIN
# -------------------------------
@app.post("/login")
async def login(data: LoginData):
    conn = await get_connection()
    logger.info(f"Datos recibidos del login: {data}")
    try:
        query = "SELECT * FROM usuarios WHERE id=$1"
        user = await conn.fetchrow(query, data.user)
        
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        if data.password != user['password']:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        
        logger.info(f"Login correcto para usuario: {data.user}")
        return {"message": "Login correcto"}
    finally:
        await conn.close()

# -------------------------------
# ENDPOINT PRODUCTOS
# -------------------------------
@app.post("/productos")
async def crear_producto(prod: Producto):
    print("[BACK] Datos recibidos:", prod.dict())
    conn = await get_connection()
    try:
        # 👇 log de las tablas disponibles
        tablas = await conn.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        )
        print("[DB] Tablas en la base de datos:", [t["table_name"] for t in tablas])

        existe = await conn.fetchrow(
            "SELECT id FROM productos WHERE referencia=$1", prod.referencia
        )
        if existe:
            raise HTTPException(
                status_code=400,
                detail=f"La referencia '{prod.referencia}' ya existe"
            )

        query = """
            INSERT INTO productos (nombre, referencia, precio_compra)
            VALUES ($1, $2, $3)
            RETURNING id
        """
        new_id = await conn.fetchval(
            query, prod.nombre, prod.referencia, prod.precio_compra
        )
        
        print(f"[OK] Producto insertado -> ID {new_id}, REF {prod.referencia}")

        return {"id": new_id, "msg": "Producto creado correctamente"}
    finally:
        await conn.close()




# -------------------------------
# RAILWAY: Puerto dinámico
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
