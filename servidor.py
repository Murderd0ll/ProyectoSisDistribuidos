from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import sqlite3
import threading
import time

app = Flask(__name__)

# =========================
# CONFIGURACIÓN BASE DE DATOS
# =========================
def init_db():
    conn = sqlite3.connect('monitor.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nodo_id TEXT,
                    cpu REAL,
                    memoria REAL,
                    fecha TEXT
                )''')
    conn.commit()
    conn.close()

def guardar_en_db(nodo_id, cpu, memoria):
    conn = sqlite3.connect('monitor.db')
    c = conn.cursor()
    c.execute("INSERT INTO registros (nodo_id, cpu, memoria, fecha) VALUES (?, ?, ?, ?)",
              (nodo_id, cpu, memoria, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# =========================
# DATOS EN MEMORIA
# =========================
nodos = {}
TIEMPO_INACTIVO = 15  # segundos sin actualizar = inactivo

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    nodo_id = data.get('nodo_id')
    cpu = data.get('cpu')
    memoria = data.get('memoria')

    nodos[nodo_id] = {
        'cpu': cpu,
        'memoria': memoria,
        'ultimo_reporte': datetime.now()
    }

    guardar_en_db(nodo_id, cpu, memoria)

    return jsonify({"mensaje": f"Datos recibidos de {nodo_id}"}), 200

@app.route('/status')
def status():
    estado_actual = {}
    for nodo, datos in nodos.items():
        activo = (datetime.now() - datos['ultimo_reporte']) < timedelta(seconds=TIEMPO_INACTIVO)
        estado_actual[nodo] = {
            'cpu': datos['cpu'],
            'memoria': datos['memoria'],
            'ultimo_reporte': datos['ultimo_reporte'].strftime('%H:%M:%S'),
            'activo': activo
        }
    return jsonify(estado_actual)

@app.route('/')
def index():
    return render_template('index.html')

# =========================
# LIMPIADOR AUTOMÁTICO (ELIMINA NODOS INACTIVOS DE LA LISTA)
# =========================
def limpiar_nodos():
    while True:
        ahora = datetime.now()
        for nodo in list(nodos.keys()):
            if (ahora - nodos[nodo]['ultimo_reporte']).seconds > 120:
                del nodos[nodo]
        time.sleep(10)
        
@app.route('/historial/<nodo_id>')
def historial_nodo(nodo_id):
    conn = sqlite3.connect('monitor.db')
    c = conn.cursor()
    c.execute("""
        SELECT cpu, memoria, fecha FROM registros
        WHERE nodo_id = ?
        ORDER BY fecha DESC LIMIT 20
    """, (nodo_id,))
    datos = c.fetchall()
    conn.close()

    # Devolvemos en formato JSON
    historial = [{"cpu": row[0], "memoria": row[1], "fecha": row[2]} for row in reversed(datos)]
    return jsonify(historial)
        

if __name__ == '__main__':
    init_db()
    threading.Thread(target=limpiar_nodos, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
