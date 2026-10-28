import socket
import json

# ==============================================================================
# CONFIGURACIÓN DEL CLIENTE
# ==============================================================================
HOST = "localhost"
PORT = 5000

def enviar_tarea(tipo_tarea, parametros):
    """Envía una tarea en formato JSON por socket TCP y espera la respuesta."""
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect((HOST, PORT))

        # Estructura del mensaje de tarea
        solicitud = {
            "tipo": tipo_tarea,
            "parametros": parametros
        }

        # Serializar y enviar
        cliente.sendall(json.dumps(solicitud).encode("utf-8"))

        # Recibir resultado del worker
        respuesta_bytes = cliente.recv(8192)
        if not respuesta_bytes:
            print("[!] El servidor no envió respuesta.")
            return

        respuesta = json.loads(respuesta_bytes.decode("utf-8"))
        mostrar_resultado(respuesta)

    except ConnectionRefusedError:
        print("\n[ERROR] No se pudo conectar al servidor. Verifica que 'servidor.py' esté en ejecución.")
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error inesperado: {e}")
    finally:
        cliente.close()

def mostrar_resultado(respuesta):
    """Formatea la visualización de la respuesta recibida."""
    print("\n" + "-" * 55)
    print("             RESPUESTA DEL SISTEMA DISTRIBUIDO")
    print("-" * 55)
    print(f"Estado:            {respuesta.get('status')}")
    print(f"Worker Procesador: {respuesta.get('worker_asignado')}")

    if respuesta.get("status") == "OK":
        print(f"Tipo de Tarea:     {respuesta.get('tipo_tarea')}")
        print(f"Tiempo Ejecución:  {respuesta.get('tiempo_ejecucion_seg')} s")
        print("\nDetalle del Resultado:")
        print(json.dumps(respuesta.get("resultado"), indent=4, ensure_ascii=False))
    else:
        print(f"Mensaje de Error:  {respuesta.get('mensaje')}")
    print("-" * 55 + "\n")

def menu():
    print("========================================")
    print("   SISTEMA DISTRIBUIDO - ENVÍO DE TAREAS")
    print("========================================")
    print("1. Tarea de Cómputo (Cálculo de Primos)")
    print("2. Tarea de Criptografía (Hasheo de Cadena)")
    print("3. Tarea Intensiva / I/O (Simulación de retardo)")
    print("4. Salir")
    return input("Seleccione una opción: ").strip()

def main():
    while True:
        opcion = menu()

        if opcion == "1":
            limite = input("Ingrese el número límite (ej: 5000): ").strip()
            if not limite.isdigit():
                print("[!] Ingrese un valor numérico válido.")
                continue
            enviar_tarea("primos", {"limite": int(limite)})

        elif opcion == "2":
            texto = input("Ingrese el texto a procesar: ").strip()
            if not texto:
                print("[!] El texto no puede estar vacío.")
                continue
            enviar_tarea("hash", {"texto": texto})

        elif opcion == "3":
            segundos = input("Ingrese duración simulada en segundos (1-10): ").strip()
            if not segundos.isdigit():
                print("[!] Ingrese un número válido de segundos.")
                continue
            enviar_tarea("intensiva", {"segundos": int(segundos)})

        elif opcion == "4":
            print("Cerrando cliente. ¡Hasta luego!")
            break
        else:
            print("[!] Opción no válida. Intente nuevamente.\n")

if __name__ == "__main__":
    main()