from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import asyncpg
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import os
import uvicorn
import logging
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

# -------------------------------
# CONFIG
# -------------------------------
SECRET_KEY = "mi_secreto_super_seguro"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# -------------------------------
# APP
# -------------------------------
app = FastAPI()

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod cambiar por tu dominio
    allow_methods=["*"],
    allow_headers=["*"]
)

# Static & Views
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# -------------------------------
# LOGGING
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    "postgresql://postgres:kEHmlYsNdNfQAHngoJfGyYDXJXSJiWaw@shortline.proxy.rlwy.net:40143/railway"
)

async def get_connection():
    return await asyncpg.connect(DATABASE_URL)

# -------------------------------
# FUNCIONES JWT
# -------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# -------------------------------
# VISTAS
# -------------------------------
def serve_html(filename: str):
    path = Path("frontend") / filename
    if path.exists():
        return HTMLResponse(content=path.read_text(encoding="utf-8"))
    return HTMLResponse(content="Archivo no encontrado", status_code=404)

@app.get("/", response_class=HTMLResponse)
async def index_page():
    return serve_html("index.html")

@app.get("/app.html", response_class=HTMLResponse)
async def app_page(current_user: str = Depends(get_current_user)):
    return serve_html("app.html")

@app.get("/almacen-gestion")
async def almacen_gestion(current_user: str = Depends(get_current_user)):
    return FileResponse("frontend/almacen-gestion.html")

@app.get("/clientes-gestion")
async def clientes_gestion(current_user: str = Depends(get_current_user)):
    return FileResponse("frontend/clientes-gestion.html")

@app.get("/vehiculos-gestion")
async def vehiculos_gestion(current_user: str = Depends(get_current_user)):
    return FileResponse("frontend/vehiculos-gestion.html")

# -------------------------------
# LOGIN
# -------------------------------
@app.post("/login")
async def login(data: LoginData):
    conn = await get_connection()
    logger.info(f"Login attempt: {data.user}")
    try:
        query = "SELECT * FROM usuarios WHERE id=$1"
        user = await conn.fetchrow(query, data.user)

        if not user or data.password != user['password']:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

        token = create_access_token({"sub": data.user})
        logger.info(f"Login correcto: {data.user}")
        return {"access_token": token, "token_type": "bearer"}
    finally:
        await conn.close()

# -------------------------------
# ENDPOINT PRODUCTOS
# -------------------------------
@app.post("/productos")
async def crear_producto(prod: Producto, current_user: str = Depends(get_current_user)):
    print("[BACK] Datos recibidos:", prod.dict())
    conn = await get_connection()
    try:
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
        new_id = await conn.fetchval(query, prod.nombre, prod.referencia, prod.precio_compra)
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
