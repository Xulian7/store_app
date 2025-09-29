import asyncpg
import asyncio

DATABASE_URL = "postgresql://postgres:kEHmlYsNdNfQAHngoJfGyYDXJXSJiWaw@shortline.proxy.rlwy.net:40143/railway"

async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)

    # Borrar si ya existen (cuidado, destruye datos)
    await conn.execute("DROP TABLE IF EXISTS movimientos CASCADE;")
    await conn.execute("DROP TABLE IF EXISTS productos CASCADE;")
    await conn.execute("DROP TABLE IF EXISTS proveedores CASCADE;")
    await conn.execute("DROP TABLE IF EXISTS clientes CASCADE;")

    # Crear tablas
    await conn.execute("""
    CREATE TABLE proveedores (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT
    );
    """)

    await conn.execute("""
    CREATE TABLE clientes (
        cedula VARCHAR(20) PRIMARY KEY,
        tipo VARCHAR(20) CHECK (tipo IN ('interno', 'externo')) NOT NULL,
        nombre TEXT NOT NULL,
        placa TEXT,
        telefono TEXT,
        direccion TEXT
    );
    """)

    await conn.execute("""
    CREATE TABLE productos (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        referencia TEXT UNIQUE NOT NULL,
        precio_venta NUMERIC(12,2) NOT NULL
    );
    """)

    await conn.execute("""
    CREATE TABLE movimientos (
        id SERIAL PRIMARY KEY,
        producto_id INT REFERENCES productos(id) ON DELETE CASCADE,
        tipo VARCHAR(30) CHECK (tipo IN ('Compra', 'Venta', 'Devolucion_Proveedor', 'Retorno_Cliente', 'Ajuste')) NOT NULL,
        cantidad INT NOT NULL CHECK (cantidad <> 0),
        precio_unitario NUMERIC(12,2) NOT NULL,
        proveedor_id INT REFERENCES proveedores(id),
        cliente_id VARCHAR(20) REFERENCES clientes(cedula),
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CHECK (
            (tipo = 'Compra' AND proveedor_id IS NOT NULL AND cliente_id IS NULL) OR
            (tipo = 'Devolucion_Proveedor' AND proveedor_id IS NOT NULL AND cliente_id IS NULL) OR
            (tipo = 'Venta' AND cliente_id IS NOT NULL AND proveedor_id IS NULL) OR
            (tipo = 'Retorno_Cliente' AND cliente_id IS NOT NULL AND proveedor_id IS NULL) OR
            (tipo = 'Ajuste' AND proveedor_id IS NULL AND cliente_id IS NULL)
        )
    );
    """)

    await conn.close()
    print("Tablas creadas con éxito 🚀")

asyncio.run(create_tables())
