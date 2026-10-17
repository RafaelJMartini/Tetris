# Tetris Multiplayer

Um jogo de Tetris competitivo para dois jogadores desenvolvido em **Python**, utilizando **Pygame** para a interface gráfica e comunicação em tempo real via **Sockets TCP**. 

---

## Funcionalidades

- **Multiplayer via TCP:** Comunicação confiável orientada a conexão, gerenciada por um servidor central.
- **Sincronização de Peças (Seed):** Ambos os jogadores recebem exatamente a mesma sequência de tetraminós na mesma ordem. A sequência é gerada por um **sistema 7-bag** com um gerador dedicado, criado a partir da seed enviada pelo servidor — por isso ela continua idêntica mesmo quando só um dos jogadores leva linhas de lixo.
- **Próxima Peça:** painel "PRÓXIMA" entre os dois tabuleiros, igual nos dois clientes.
- **Fim de Partida pelo Servidor:** quem perde avisa o servidor, que define o vencedor e encerra a partida nos dois clientes ao mesmo tempo (`VOCÊ VENCEU` / `VOCÊ PERDEU`).
- **Tabuleiro do Oponente em Tempo Real:** a tela do adversário mostra a peça em queda e a pontuação dele.
- **Robustez:** se um jogador cair no meio da partida, o servidor entrega a vitória ao adversário em vez de deixar o jogo travado.
- **Níveis:** a cada 10 linhas o nível sobe, a gravidade acelera (de 500 ms até 110 ms por linha) e a pontuação passa a valer mais.
- **Revanche:** ao fim da partida, basta os dois jogadores apertarem `R` para começar outra com uma sequência nova, sem reiniciar o servidor.
- **Mecânicas Clássicas:**
  - Rotação de peças com Wall Kick básico.
  - **Hard Drop** instantâneo utilizando a tecla `Espaço`.
  - **Ghost piece:** contorno mostrando onde a peça vai parar.
  - Contador de linhas de lixo enviadas e recebidas no painel.
  - Repetição suave de teclas ao segurar as setas direcionais.
- **Sistema de Batalha (Linhas de Lixo):** Limpar múltiplas linhas envia linhas cinzas de penalidade para a base do tabuleiro do adversário:
  - **Double (2 linhas):** Envia 1 linha de lixo.
  - **Triple (3 linhas):** Envia 2 linhas de lixo.
  - **Tetris (4 linhas):** Envia 4 linhas de lixo.

---

## Pré-requisitos

Certifique-se de ter o **Python 3.x** instalado em sua máquina. Você precisará da biblioteca gráfica **Pygame**.

Instale o Pygame executando o seguinte comando no seu terminal:
```bash
pip install pygame
```

---

## Como executar o jogo

Abra 3 terminais:

### Primeiro terminal
```bash
python server.py            # ou: python server.py 50005
```

### Segundo e terceiro terminal

```bash
python client.py            # conecta em 127.0.0.1:50005
```

### Jogando em duas máquinas

O servidor escuta em `0.0.0.0`, então basta cada cliente apontar para o IP dele:

```bash
python client.py 192.168.0.10 50005
```

### Controles

| Tecla | Ação |
|---|---|
| ← / → | mover |
| ↑ | girar |
| ↓ | descer uma linha |
| Espaço | hard drop |
| R | pedir revanche (na tela de fim de partida) |

---

## Protocolo (JSON, uma mensagem por linha terminada em `\n`)

**Servidor → Cliente**

| Tipo | Campos |
|---|---|
| `WELCOME` | `player_id` |
| `START` | `seed` |
| `BOARD_UPDATE` | `player_id`, `board`, `score` |
| `GARBAGE` | `target_id`, `lines`, `holes` |
| `MATCH_END` | `winner_id`, `loser_id`, `reason` |
| `OPPONENT_LEFT` | — |

**Cliente → Servidor**

| Tipo | Campos |
|---|---|
| `BOARD_UPDATE` | `player_id`, `board`, `score` |
| `GARBAGE` | `target_id`, `lines`, `holes` |
| `GAME_OVER` | `player_id` |
| `REMATCH` | `player_id` |

As posições dos buracos das linhas de lixo (`holes`) são sorteadas por quem ataca e viajam
junto da mensagem — assim o cliente que recebe o ataque não precisa sortear nada e a
sequência de peças nunca sai de sincronia.

O estado pendente vindo da rede (seed e lixo) é consumido pela thread principal, não pela
thread de recepção, para não haver acesso concorrente ao tabuleiro.
