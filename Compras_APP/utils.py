import urllib.request
import urllib.parse
import json
import os
import sqlite3

def consultar_existencias_api(producto_identificador):
    """
    Consumir la API de Logística para consultar las existencias de un producto.
    Si el servidor no está corriendo, recurre a una consulta directa a la base de datos de Logística.
    """
    if not producto_identificador:
        return None

    # Intentar consumir el servicio HTTP de la API de Logística
    url = f"http://127.0.0.1:8001/api/existencias/?producto={urllib.parse.quote(producto_identificador)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Compras_APP"})
        with urllib.request.urlopen(req, timeout=1.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get("status") == "success":
                    return data.get("producto")
    except Exception:
        # Si la API no responde, se usa el fallback directo de base de datos
        pass

    # Fallback: Consulta directa de base de datos sqlite3 de Logística
    # Buscamos la base de datos de Logística en los directorios relativos esperados
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "Logistica", "db.sqlite3"),
        "/app/Logistica/db.sqlite3"
    ]

    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break

    if db_path:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT codigo, nombre, stock_bodega, stock_percha FROM inventory_producto WHERE LOWER(codigo) = ? OR LOWER(nombre) = ?",
                (producto_identificador.lower(), producto_identificador.lower())
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                codigo, nombre, stock_bodega, stock_percha = row
                return {
                    "codigo": codigo,
                    "nombre": nombre,
                    "stock_bodega": stock_bodega,
                    "stock_percha": stock_percha,
                    "stock_total": stock_bodega + stock_percha,
                    "stock_minimo": 0
                }
        except Exception as e:
            print(f"[DEBUG Fallback] Error al consultar sqlite3 de Logística: {e}")

    return None
