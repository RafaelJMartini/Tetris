import socket
import json
import random

HOST = '127.0.0.1'
PORT = 50005

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print(f"[SERVIDOR] Rodando em {HOST}:{PORT}")

clients = []
game_seed = random.randint(1, 1000000)

while True:
    try:
        data, addr = server_socket.recvfrom(4096)
        message = json.loads(data.decode('utf-8'))
        
        msg_type = message.get("type")
        
        if msg_type == "JOIN":
            if addr not in clients:
                if len(clients) < 2:
                    clients.append(addr)
                    player_id = len(clients)
                    print(f"[SERVIDOR] Jogador {player_id} conectado: {addr}")
                    
                    response = json.dumps({"type": "WELCOME", "player_id": player_id})
                    server_socket.sendto(response.encode('utf-8'), addr)
                    
                    if len(clients) == 2:
                        print("[SERVIDOR] Sala cheia! Iniciando o jogo...")
                        start_msg = json.dumps({"type": "START", "seed": game_seed})
                        for c in clients:
                            server_socket.sendto(start_msg.encode('utf-8'), c)
                else:
                    response = json.dumps({"type": "FULL"})
                    server_socket.sendto(response.encode('utf-8'), addr)
            else:
                player_id = clients.index(addr) + 1
                response = json.dumps({"type": "WELCOME", "player_id": player_id})
                server_socket.sendto(response.encode('utf-8'), addr)
                if len(clients) == 2:
                    start_msg = json.dumps({"type": "START", "seed": game_seed})
                    server_socket.sendto(start_msg.encode('utf-8'), addr)
                    
        elif msg_type in ["BOARD_UPDATE", "GARBAGE"]:
            for c in clients:
                if c != addr:
                    server_socket.sendto(data, c)
                    
    except Exception as e:
        print(f"[ERRO NO SERVIDOR] {e}")