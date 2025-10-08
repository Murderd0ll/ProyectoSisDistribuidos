from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Diccionario para guardar el estado de cada nodo
nodos = {}

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    nodo_id = data.get('nodo_id')
    cpu = data.get('cpu')
    memoria = data.get('memoria')

    nodos[nodo_id] = {
        'cpu': cpu,
        'memoria': memoria,
        'ultimo_reporte': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify({"mensaje": f"Datos recibidos de {nodo_id}"}), 200


@app.route('/status', methods=['GET'])
def status():
    return jsonify(nodos), 200


@app.route('/')
def home():
    html = "<h1>Sistema de Monitoreo Distribuido</h1><ul>"
    for nodo, datos in nodos.items():
        html += f"<li><b>{nodo}</b> - CPU: {datos['cpu']}% | RAM: {datos['memoria']}% | Último reporte: {datos['ultimo_reporte']}</li>"
    html += "</ul>"
    return html


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
