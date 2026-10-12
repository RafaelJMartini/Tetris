import socket
import json
import threading
import random

HOST = '127.0.0.1'
PORT = 50005

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# O REUSEADDR evita o erro "Address already in use" se reiniciar rápido
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(2)

print(f"[SERVIDOR TCP] Rodando em {HOST}:{PORT}")

clients = []  # Lista de tuplas: (socket, endereço, player_id)
game_seed = random.randint(1, 1000000)

def handle_client(client_socket, addr, player_id):
    global clients
    print(f"[SERVIDOR] Jogador {player_id} conectado: {addr}")
    
    welcome_msg = json.dumps({"type": "WELCOME", "player_id": player_id}) + "\n"
    client_socket.sendall(welcome_msg.encode('utf-8'))
    
    # Se já temos 2 clientes, envia o comando START com a seed para ambos
    if len(clients) == 2:
        print("[SERVIDOR] Sala cheia! Iniciando o jogo...")
        start_msg = json.dumps({"type": "START", "seed": game_seed}) + "\n"
        for c, _, _ in clients:
            c.sendall(start_msg.encode('utf-8'))

    buffer = ""
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            
            buffer += data.decode('utf-8')
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                
                message = json.loads(line)
                msg_type = message.get("type")
                
                if msg_type in ["BOARD_UPDATE", "GARBAGE"]:
                    for c, _, pid in clients:
                        if pid != player_id:
                            c.sendall((line + "\n").encode('utf-8'))
                            
        except Exception as e:
            print(f"[ERRO] Jogador {player_id} desconectado: {e}")
            break

    clients = [c for c in clients if c[0] != client_socket]
    client_socket.close()

# Loop principal aceitando conexões
while len(clients) < 2:
    sock, addr = server_socket.accept()
    player_id = len(clients) + 1
    clients.append((sock, addr, player_id))
    
    threading.Thread(target=handle_client, args=(sock, addr, player_id), daemon=True).start()

# Mantém o servidor rodando em segundo plano
while True:
    pass