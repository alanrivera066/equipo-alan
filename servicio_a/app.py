import os
import requests
import mysql.connector
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Credenciales desde variables de entorno
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST"),
    "user":     os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME")
}

# URL interna del Servicio B (nombre del servicio en docker-compose)
SERVICIO_B = "http://servicio_b:5001/procesar-alerta"

# ─── Conexión a base de datos ───
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ─── HTML mínimo ───
HTML = """
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Inventario TechNova</title></head>
<body>
    <h1>Sistema de Inventario</h1>

    <h2>Registrar Producto</h2>
    <form onsubmit="registrar(event)">
        Nombre: <input id="nombre"><br><br>
        Categoría: <select id="cat"></select><br><br>
        Cantidad: <input id="cant" type="number"><br><br>
        Precio: <input id="precio" type="number" step="0.01"><br><br>
        Stock mínimo: <input id="min" type="number"><br><br>
        <button type="submit">Registrar</button>
    </form>
    <p id="msg-producto"></p>

    <h2>Registrar Movimiento</h2>
    <form onsubmit="movimiento(event)">
        Producto: <select id="pid"></select><br><br>
        Tipo: <select id="tipo">
            <option value="entrada">Entrada — agregar stock</option>
            <option value="salida">Salida — reducir stock</option>
        </select><br><br>
        Cantidad: <input id="mcant" type="number"><br><br>
        <button type="submit">Registrar</button>
    </form>
    <p id="msg-movimiento"></p>

    <h2>Stock Actual</h2>
    <button onclick="cargar()">Actualizar</button>
    <div id="stock"></div>

    <h2>Bajo Stock</h2>
    <button onclick="bajoStock()">Ver</button>
    <div id="bajo"></div>

<script>
async function cargarCategorias() {
    const r = await fetch('/categorias');
    const d = await r.json();
    const sel = document.getElementById('cat');
    sel.innerHTML = '';
    d.forEach(c => {
        sel.innerHTML += `<option value="${c.id}">${c.id} — ${c.nombre}</option>`;
    });
}

async function cargarProductosSelect() {
    const r = await fetch('/productos');
    const d = await r.json();
    const sel = document.getElementById('pid');
    sel.innerHTML = '';
    d.forEach(p => {
        sel.innerHTML += `<option value="${p.id}">${p.id} — ${p.nombre} (stock: ${p.cantidad})</option>`;
    });
}

async function registrar(e) {
    e.preventDefault();
    const r = await fetch('/productos', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
            nombre:       document.getElementById('nombre').value,
            categoria_id: document.getElementById('cat').value,
            cantidad:     document.getElementById('cant').value,
            precio:       document.getElementById('precio').value,
            stock_minimo: document.getElementById('min').value
        })
    });
    const d = await r.json();
    document.getElementById('msg-producto').textContent = JSON.stringify(d);
    cargarProductosSelect();
}

async function movimiento(e) {
    e.preventDefault();
    const r = await fetch('/movimientos', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
            producto_id: document.getElementById('pid').value,
            tipo:        document.getElementById('tipo').value,
            cantidad:    document.getElementById('mcant').value
        })
    });
    const d = await r.json();
    document.getElementById('msg-movimiento').textContent = JSON.stringify(d);
    cargarProductosSelect();
}

async function cargar() {
    const r = await fetch('/productos');
    const d = await r.json();
    document.getElementById('stock').innerHTML =
        '<pre>' + JSON.stringify(d, null, 2) + '</pre>';
}

async function bajoStock() {
    const r = await fetch('/productos/bajo-stock');
    const d = await r.json();
    document.getElementById('bajo').innerHTML =
        '<pre>' + JSON.stringify(d, null, 2) + '</pre>';
}

cargarCategorias();
cargarProductosSelect();
</script>
</body>
</html>
"""

# ─── RUTA 1 — Interfaz HTML ───
@app.route("/")
def index():
    return render_template_string(HTML)

# ─── RUTA 2 — Listar categorías ───
@app.route("/categorias", methods=["GET"])
def listar_categorias():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre FROM categorias")
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# ─── RUTA 3 — Listar productos ───
@app.route("/productos", methods=["GET"])
def listar_productos():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.id, p.nombre, c.nombre AS categoria,
                   p.cantidad, p.precio, p.stock_minimo
            FROM productos p
            JOIN categorias c ON p.categoria_id = c.id
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# ─── RUTA 4 — Registrar producto ───
@app.route("/productos", methods=["POST"])
def registrar_producto():
    conn = None
    try:
        d = request.json
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, categoria_id, cantidad, precio, stock_minimo) VALUES (%s,%s,%s,%s,%s)",
            (d["nombre"], d["categoria_id"], d["cantidad"], d["precio"], d["stock_minimo"])
        )
        conn.commit()
        return jsonify({"mensaje": "Producto registrado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if conn:
            conn.close()

# ─── RUTA 5 — Registrar movimiento ───
@app.route("/movimientos", methods=["POST"])
def registrar_movimiento():
    conn = None
    try:
        d = request.json
        producto_id = int(d["producto_id"])
        tipo        = d["tipo"]
        cantidad    = int(d["cantidad"])

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Obtener stock actual
        cursor.execute("SELECT cantidad, stock_minimo FROM productos WHERE id = %s", (producto_id,))
        producto = cursor.fetchone()
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        # Calcular nuevo stock
        if tipo == "salida":
            if cantidad > producto["cantidad"]:
                return jsonify({"error": "Stock insuficiente"}), 400
            nuevo_stock = producto["cantidad"] - cantidad
        else:
            nuevo_stock = producto["cantidad"] + cantidad

        # Actualizar stock y registrar movimiento
        cursor.execute("UPDATE productos SET cantidad = %s WHERE id = %s", (nuevo_stock, producto_id))
        cursor.execute(
            "INSERT INTO movimientos (producto_id, tipo, cantidad) VALUES (%s,%s,%s)",
            (producto_id, tipo, cantidad)
        )
        conn.commit()

        respuesta = {"mensaje": f"Movimiento registrado. Stock actual: {nuevo_stock}"}

        # Si stock quedó bajo, llamar a B directamente (bloqueante — genera el tiempo de espera visible)
        if tipo == "salida" and nuevo_stock <= producto["stock_minimo"]:
            try:
                r = requests.post(SERVICIO_B, json={
                    "producto_id": producto_id,
                    "stock_actual": nuevo_stock,
                    "stock_minimo": producto["stock_minimo"]
                }, timeout=15)
                respuesta["alerta"] = r.json().get("mensaje", "Notificación enviada al Servicio B")
            except Exception:
                respuesta["alerta"] = "Dato guardado, pero Servicio B en mantenimiento"

        return jsonify(respuesta), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if conn:
            conn.close()

# ─── RUTA 6 — Productos bajo stock ───
@app.route("/productos/bajo-stock", methods=["GET"])
def bajo_stock():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, cantidad, stock_minimo
            FROM productos
            WHERE cantidad <= stock_minimo
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# ─── RUTA 7 — Ver alertas ───
@app.route("/alertas", methods=["GET"])
def ver_alertas():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM alertas_reposicion ORDER BY creado_en DESC")
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
