import psutil
import requests
import time
import socket

SERVIDOR_URL = "http://127.0.0.1:5000/update"  # Cambia si usas otra IP
INTERVALO = 5  # segundos entre reportes

def obtener_datos():
    cpu = psutil.cpu_percent(interval=1)
    memoria = psutil.virtual_memory().percent
    return cpu, memoria

def enviar_datos():
    nombre_nodo = socket.gethostname()
    while True:
        cpu, memoria = obtener_datos()
        datos = {
            "nodo_id": nombre_nodo,
            "cpu": cpu,
            "memoria": memoria
        }
        try:
            r = requests.post(SERVIDOR_URL, json=datos, timeout=5)
            print(f"[{nombre_nodo}] Enviado: CPU {cpu}% | RAM {memoria}% | Estado: {r.status_code}")
        except Exception as e:
            print(f"[{nombre_nodo}] Error al enviar datos: {e}")
        time.sleep(INTERVALO)

if __name__ == '__main__':
    enviar_datos()
