import socket
import json
import time
import math
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor

# ==============================================================================
# CONFIGURACIÓN GENERAL DEL SERVIDOR
# ==============================================================================
HOST = "localhost"
PORT = 5000
MAX_WORKERS = 4  # Tamaño del pool de hilos trabajadores

# ==============================================================================
# LÓGICA DE PROCESAMIENTO DE LAS TAREAS (EJECUTADA POR LOS WORKERS)
# ==============================================================================
def tarea_primos(limite):
    """Calcula la cantidad y lista de números primos hasta un límite dado."""
    if limite > 100000:
        limite = 100000  # Límite de seguridad
    
    primos = []
    for num in range(2, limite + 1):
        es_primo = True
        for i in range(2, int(math.isqrt(num)) + 1):
            if num % i == 0:
                es_primo = False
                break
        if es_primo:
            primos.append(num)
            
    return {
        "limite_evaluado": limite,
        "total_primos": len(primos),
        "ultimos_5": primos[-5:] if len(primos) >= 5 else primos
    }

def tarea_hash(texto):
    """Calcula múltiples funciones de resumen criptográfico de un texto."""
    md5_hash = hashlib.md5(texto.encode("utf-8")).hexdigest()
    sha256_hash = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    return {
        "longitud_caracteres": len(texto),
        "md5": md5_hash,
        "sha256": sha256_hash
    }

def tarea_intensiva(duracion_segundos):
    """Simula una tarea intensiva o de I/O bloqueante durante 'n' segundos."""
    duracion = min(max(1, duracion_segundos), 10)  # Entre 1 y 10 segundos
    time.sleep(duracion)
    return {
        "descripcion": f"Proceso simulado completado exitosamente",
        "tiempo_espera_solicitado": duracion
    }

def ejecutar_tarea(tipo, parametros):
    """Resuelve la tarea solicitada y devuelve el resultado computado."""
    if tipo == "primos":
        limite = int(parametros.get("limite", 1000))
        return tarea_primos(limite)
    elif tipo == "hash":
        texto = str(parametros.get("texto", ""))
        return tarea_hash(texto)
    elif tipo == "intensiva":
        segundos = int(parametros.get("segundos", 2))
        return tarea_intensiva(segundos)
    else:
        raise ValueError(f"Tipo de tarea desconocido: '{tipo}'")


# ==============================================================================
# GESTIÓN Y DESPACHO DE CLIENTES
# ==============================================================================
def atender_cliente(conn, addr):
    """
    Función que ejecuta un worker del pool para procesar la petición del cliente.
    """
    nombre_worker = threading.current_thread().name
    print(f"[WORKER] [{nombre_worker}] Atendiendo solicitud desde {addr}")

    try:
        # Lectura de la petición
        datos = conn.recv(4096)
        if not datos:
            return

        inicio_tiempo = time.time()
        peticion = json.loads(datos.decode("utf-8"))

        tipo_tarea = peticion.get("tipo")
        parametros = peticion.get("parametros", {})

        print(f"[WORKER] [{nombre_worker}] Procesando tarea '{tipo_tarea}'...")

        # Ejecución de la lógica
        resultado = ejecutar_tarea(tipo_tarea, parametros)
        tiempo_total = round(time.time() - inicio_tiempo, 4)

        # Construcción de la respuesta estructurada
        respuesta = {
            "status": "OK",
            "worker_asignado": nombre_worker,
            "tipo_tarea": tipo_tarea,
            "tiempo_ejecucion_seg": tiempo_total,
            "resultado": resultado
        }

    except json.JSONDecodeError:
        respuesta = {
            "status": "ERROR",
            "worker_asignado": nombre_worker,
            "mensaje": "El payload recibido no es un JSON válido."
        }
    except Exception as e:
        respuesta = {
            "status": "ERROR",
            "worker_asignado": nombre_worker,
            "mensaje": f"Fallo al procesar la tarea: {str(e)}"
        }

    # Enviar respuesta al cliente
    try:
        conn.sendall(json.dumps(respuesta).encode("utf-8"))
    except Exception as e:
        print(f"[ERROR] No se pudo responder al cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"[WORKER] [{nombre_worker}] Finalizada atención de {addr}.\n")


# ==============================================================================
# BUCLE PRINCIPAL DEL SERVIDOR (DISPATCHER)
# ==============================================================================
def iniciar_servidor():
    """Inicializa el socket servidor y despacha conexiones a un ThreadPool."""
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        servidor.bind((HOST, PORT))
        servidor.listen(10)
        print("=" * 65)
        print(f"[*] SERVIDOR DISTRIBUIDOR INICIADO EN {HOST}:{PORT}")
        print(f"[*] Pool configurado con {MAX_WORKERS} workers concurrentes.")
        print("=" * 65)

        # Creación del pool de hilos trabajadores
        with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="Worker") as pool:
            while True:
                conn, addr = servidor.accept()
                # Delegar la atención del socket al pool de workers sin bloquear
                pool.submit(atender_cliente, conn, addr)

    except KeyboardInterrupt:
        print("\n[*] Apagando el servidor distribuidor...")
    except OSError as e:
        print(f"[ERROR RED] Error en el socket servidor: {e}")
    finally:
        servidor.close()
        print("[-] Servidor cerrado.")

if __name__ == "__main__":
    iniciar_servidor()