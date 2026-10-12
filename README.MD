# Tetris Multiplayer

Um jogo de Tetris competitivo para dois jogadores desenvolvido em **Python**, utilizando **Pygame** para a interface gráfica e comunicação em tempo real via **Sockets UDP**. 

---

## Funcionalidades

- **Multiplayer via UDP:** Comunicação rápida e descentralizada gerenciada por um servidor central.
- **Sincronização de Peças (Seed):** Ambos os jogadores recebem exatamente a mesma sequência de tetraminós na mesma ordem.
- **Mecânicas Clássicas:**
  - Rotação de peças com Wall Kick básico.
  - **Hard Drop** instantâneo utilizando a tecla `Espaço`.
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
python server.py
```

### Segundo e terceiro terminal

```bash
python client.py
```