# nodo_multiple.py - Simula múltiples nodos
import psutil # obtener valores de uso de CPU y RAM
import requests # peticiones http
import time # manejar tiempos de espera
import socket # obtener el nombre del nodo (comunicación cliente-servidor)
import random # para simular variaciones en los datos

SERVIDOR_URL = "http://127.0.0.1:5000/update"
INTERVALO = 5

def simular_nodo(nombre_nodo):
    while True:
        # Simular valores ligeramente diferentes para cada nodo
        cpu = psutil.cpu_percent(interval=1) + random.uniform(-5, 5)
        memoria = psutil.virtual_memory().percent + random.uniform(-3, 3)
        
        # Asegurar que estén entre 0-100
        cpu = max(0, min(100, cpu))
        memoria = max(0, min(100, memoria))
        
        datos = {
            "nodo_id": nombre_nodo,
            "cpu": cpu,
            "memoria": memoria
        }
        try:
            r = requests.post(SERVIDOR_URL, json=datos, timeout=5)
            print(f"[{nombre_nodo}] CPU: {cpu:.1f}% | RAM: {memoria:.1f}% | Status: {r.status_code}")
        except Exception as e:
            print(f"[{nombre_nodo}] Error: {e}")
        time.sleep(INTERVALO)

if __name__ == '__main__':
    # Simular 3 nodos diferentes
    import threading
    
    nodos = ["Nodo-01", "Nodo-02", "Nodo-03"]
    for nodo in nodos:
        threading.Thread(target=simular_nodo, args=(nodo,), daemon=True).start()
    
    # Mantener el script corriendo
    while True:
        time.sleep(1)