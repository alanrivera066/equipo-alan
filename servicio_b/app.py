import os
import time
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

# Credenciales desde variables de entorno
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST"),
    "user":     os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME")
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ─── Única ruta: recibe la alerta y la procesa ───
@app.route("/procesar-alerta", methods=["POST"])
def procesar_alerta():
    conn = None
    try:
        d = request.json

        # Tarea pesada simulada
        time.sleep(5)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alertas_reposicion (producto_id, stock_actual, stock_minimo) VALUES (%s,%s,%s)",
            (d["producto_id"], d["stock_actual"], d["stock_minimo"])
        )
        conn.commit()
        return jsonify({"mensaje": "Alerta de reposición generada"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
