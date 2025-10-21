from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import sqlite3
import threading
import time
from collections import defaultdict

app = Flask(__name__)

# =========================
# CONFIGURACIÓN BASE DE DATOS
# =========================
def init_db():
    conn = sqlite3.connect('monitor.db', check_same_thread=False)
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
    conn = sqlite3.connect('monitor.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO registros (nodo_id, cpu, memoria, fecha) VALUES (?, ?, ?, ?)",
              (nodo_id, cpu, memoria, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# =========================
# DATOS EN MEMORIA
# =========================
nodos = {}
TIEMPO_INACTIVO = 10  # segundos sin actualizar = inactivo

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    nodo_id = data.get('nodo_id')
    cpu = data.get('cpu')
    memoria = data.get('memoria')

    if nodo_id:  # Validar que existe nodo_id
        nodos[nodo_id] = {
            'cpu': cpu,
            'memoria': memoria,
            'ultimo_reporte': datetime.now()
        }

        guardar_en_db(nodo_id, cpu, memoria)
        return jsonify({"mensaje": f"Datos recibidos de {nodo_id}"}), 200
    else:
        return jsonify({"error": "nodo_id requerido"}), 400

@app.route('/status')
def status():
    estado_actual = {}
    ahora = datetime.now()
    
    for nodo, datos in nodos.items():
        tiempo_transcurrido = (ahora - datos['ultimo_reporte']).total_seconds()
        activo = tiempo_transcurrido < TIEMPO_INACTIVO
        
        estado_actual[nodo] = {
            'cpu': datos['cpu'],
            'memoria': datos['memoria'],
            'ultimo_reporte': datos['ultimo_reporte'].strftime('%H:%M:%S'),
            'activo': activo,
            'tiempo_inactivo': int(tiempo_transcurrido) if not activo else 0
        }
    
    return jsonify(estado_actual)

@app.route('/')
def index():
    return render_template('index.html')

# =========================
# LIMPIADOR AUTOMÁTICO
# =========================
def limpiar_nodos():
    while True:
        ahora = datetime.now()
        nodos_a_eliminar = []
        
        for nodo_id, datos in nodos.items():
            if (ahora - datos['ultimo_reporte']).seconds > 120:
                nodos_a_eliminar.append(nodo_id)
        
        for nodo_id in nodos_a_eliminar:
            del nodos[nodo_id]
            print(f"Nodo {nodo_id} eliminado por inactividad")
        
        time.sleep(30)  # Revisar cada 30 segundos

@app.route('/historial/<nodo_id>')
def historial_nodo(nodo_id):
    conn = sqlite3.connect('monitor.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        SELECT cpu, memoria, fecha FROM registros
        WHERE nodo_id = ?
        ORDER BY fecha DESC LIMIT 20
    """, (nodo_id,))
    datos = c.fetchall()
    conn.close()

    historial = [{"cpu": row[0], "memoria": row[1], "fecha": row[2]} for row in reversed(datos)]
    return jsonify(historial)

@app.route('/historial/promedio')
def historial_promedio():
    conn = sqlite3.connect('monitor.db', check_same_thread=False)
    c = conn.cursor()
    
    # Obtener promedios por intervalo de tiempo (agrupar por minutos)
    c.execute("""
        SELECT 
            strftime('%Y-%m-%d %H:%M', fecha) as intervalo,
            AVG(cpu) AS cpu_promedio,
            AVG(memoria) AS memoria_promedio
        FROM registros
        WHERE fecha >= datetime('now', '-1 hour')
        GROUP BY intervalo
        ORDER BY intervalo DESC
        LIMIT 20
    """)
    datos = c.fetchall()
    conn.close()

    historial = [{
        "cpu": round(row[1], 2), 
        "memoria": round(row[2], 2), 
        "fecha": row[0]
    } for row in reversed(datos)]
    
    return jsonify(historial)

# Nueva ruta para obtener todos los nodos registrados
@app.route('/nodos')
def lista_nodos():
    conn = sqlite3.connect('monitor.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT DISTINCT nodo_id FROM registros ORDER BY nodo_id")
    nodos_db = [row[0] for row in c.fetchall()]
    conn.close()
    
    return jsonify(nodos_db)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=limpiar_nodos, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)