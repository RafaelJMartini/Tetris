import socket
import json
import sys
import threading
import random

# Uso: python server.py [porta]
# 0.0.0.0 pra aceitar conexão de outras máquinas
HOST = '0.0.0.0'
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 50005

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# O REUSEADDR evita o erro "Address already in use" se reiniciar rápido
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(2)

print(f"[SERVIDOR TCP] Rodando em {HOST}:{PORT}")

clients = []  # Lista de tuplas: (socket, endereço, player_id)

# O primeiro GAME_OVER que chegar decide o vencedor
match_lock = threading.Lock()
match_started = False
match_over = False
rematch_ready = set()   # quem já pediu revanche

def broadcast(payload):
    line = (json.dumps(payload) + "\n").encode('utf-8')
    for c, _, _ in list(clients):
        try:
            c.sendall(line)
        except Exception:
            pass

def iniciar_partida():
    seed = random.randint(1, 1000000)
    print(f"[SERVIDOR] Iniciando partida (seed {seed})")
    broadcast({"type": "START", "seed": seed})

def encerrar_partida(loser_id, reason):
    global match_over
    with match_lock:
        if match_over or not match_started:
            return
        match_over = True
        rematch_ready.clear()
    winner_id = 2 if loser_id == 1 else 1
    print(f"[SERVIDOR] Jogador {loser_id} perdeu ({reason}). Vencedor: Jogador {winner_id}")
    broadcast({"type": "MATCH_END", "winner_id": winner_id,
               "loser_id": loser_id, "reason": reason})

def handle_client(client_socket, addr, player_id):
    global clients, match_started, match_over
    print(f"[SERVIDOR] Jogador {player_id} conectado: {addr}")

    welcome_msg = json.dumps({"type": "WELCOME", "player_id": player_id}) + "\n"
    client_socket.sendall(welcome_msg.encode('utf-8'))

    # Se já temos 2 clientes, envia o comando START com a seed para ambos
    if len(clients) == 2:
        print("[SERVIDOR] Sala cheia!")
        with match_lock:
            match_started = True
        iniciar_partida()

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
                    for c, _, pid in list(clients):
                        if pid != player_id:
                            c.sendall((line + "\n").encode('utf-8'))

                elif msg_type == "GAME_OVER":
                    # Encerra a partida para os dois ao mesmo tempo
                    encerrar_partida(player_id, "game_over")

                elif msg_type == "REMATCH":
                    # Só recomeça quando os dois pedirem
                    recomecar = False
                    with match_lock:
                        if match_over:
                            rematch_ready.add(player_id)
                            print(f"[SERVIDOR] Jogador {player_id} quer revanche "
                                  f"({len(rematch_ready)}/2)")
                            if len(rematch_ready) == 2 and len(clients) == 2:
                                rematch_ready.clear()
                                match_over = False
                                recomecar = True
                    if recomecar:
                        iniciar_partida()

        except Exception as e:
            print(f"[ERRO] Jogador {player_id} desconectado: {e}")
            break

    clients = [c for c in clients if c[0] != client_socket]
    client_socket.close()
    print(f"[SERVIDOR] Jogador {player_id} saiu.")
    # Quem cai no meio da partida entrega a vitória para o adversário
    encerrar_partida(player_id, "desconexao")
    # Se já tinha acabado, não dá mais pra pedir revanche
    with match_lock:
        rematch_ready.clear()
    broadcast({"type": "OPPONENT_LEFT"})

# Loop principal aceitando conexões
while len(clients) < 2:
    sock, addr = server_socket.accept()
    player_id = len(clients) + 1
    clients.append((sock, addr, player_id))

    threading.Thread(target=handle_client, args=(sock, addr, player_id), daemon=True).start()

# Mantém o servidor rodando em segundo plano
threading.Event().wait()
