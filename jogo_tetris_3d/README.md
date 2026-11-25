# Tetris 3D (Three.js + WebGL)

Jogo de Tetris simples em **3D** rodando direto no navegador com **Three.js**, **Vite** e motor de regras puro testável em **Node.js**.

## Stack escolhida

- **Three.js (WebGL)**: renderização 3D por GPU com blocos chanfrados (`RoundedBoxGeometry`), sombras suaves, luzes de recorte, partículas na limpeza de linhas e câmera orbital interativa.
- **Vite**: servidor de desenvolvimento instantâneo e bundle de produção leve.
- **JavaScript (ES Modules) + `node --test`**: motor de regras isolado (`src/tetris_engine.js`) sem dependência de DOM/3D, validado por testes unitários nativos.
- **Web Audio API**: efeitos sonoros procedurais sem arquivos externos.

## Como jogar

```powershell
# Pelo atalho na raiz do repositório
.\jogar_tetris_3d.bat

# Ou manualmente dentro da pasta
cd .\jogo_tetris_3d
npm install
npm run dev
```

## Controles

| Tecla / Mouse | Ação |
| --- | --- |
| `←` / `→` ou `A` / `D` | Mover para esquerda / direita |
| `↑` / `W` / `X` | Girar no sentido horário |
| `Z` | Girar no sentido anti-horário |
| `↓` / `S` | Descer rápido (*soft drop*) |
| `Espaço` | Queda instantânea (*hard drop*) |
| `Shift` / `E` | Guardar / trocar peça (*hold*) |
| `C` | Alternar ângulos de câmera 3D |
| `P` | Pausar / retomar |
| `M` | Ligar / desligar som |
| `R` | Reiniciar partida |
| `Mouse (arrastar / scroll)` | Orbitar e dar zoom livremente no cenário 3D |

## Testes e Build

```powershell
cd .\jogo_tetris_3d
npm test
npm run build
```
