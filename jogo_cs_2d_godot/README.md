# CS 2D Multiplayer — Godot 4 (ENet / UDP)

Versão multiplayer em rede do **CS 2D** feita para **Godot 4.2+** usando **`ENetMultiplayerPeer` (UDP)**, servidor autoritativo, `MultiplayerSpawner`, `MultiplayerSynchronizer` e iluminação/sombras 2D reais (`PointLight2D` + `LightOccluder2D`).

## Estrutura

- `project.godot`: Configuração do projeto Godot 4 (viewport `1024×680`, camadas de física).
- `scenes/main.tscn` e `scripts/main.gd`: Lobby ENet (Host / Cliente), spawn dos jogadores/bots/balas, controle de rounds e HUD.
- `scripts/arena.gd`: Mapa tático pequeno com paredes, caixas de cobertura e `LightOccluder2D` para projeção de sombras.
- `scenes/player.tscn` e `scripts/player.gd`: Controle `WASD`, mira no mouse, tiro (botão esquerdo), recarga (`R`), luz 2D local e envio de input ao servidor via RPC.
- `scenes/bot.tscn` e `scripts/bot.gd`: 2 oponentes Bots com linha de visão via raycast (`PhysicsRayQueryParameters2D`).
- `scenes/bullet.tscn` e `scripts/bullet.gd`: Projéteis sincronizados com detecção de colisão no servidor.

## Como instalar o Godot 4 e rodar

1. Instale o Godot 4 (se ainda não tiver) via `winget` ou em https://godotengine.org/download/windows/:
   ```powershell
   winget install GodotEngine.GodotEngine
   ```
2. Abra o Godot 4, clique em **Import** e selecione `jogo_cs_2d_godot/project.godot`.
3. Para testar multiplayer com **2 janelas no mesmo PC**:
   - No editor do Godot: menu **Debug → Customize Run Instances...** → marque **Enable Multiple Instances** e escolha **2** (ou abra uma segunda instância);
   - Na janela 1, clique em **Criar Sala (Host)** (porta `7777`);
   - Na janela 2, mantenha o IP `127.0.0.1` e clique em **Entrar (Cliente)**.
4. Para jogar em **rede local (LAN)**: informe o IP local do Host (ex.: `192.168.x.x`) na tela do Cliente.
