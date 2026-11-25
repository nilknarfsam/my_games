# Jogo da Forca em Python

Jogo da Forca com interface gráfica em Tkinter (biblioteca padrão do Python), banco de **100 palavras aleatórias** com dicas e **cronômetro de 20 segundos por letra** (se o tempo acabar, conta como erro).

## Arquivos

- `forca.py`: Interface gráfica (`ForcaApp`) com desenho progressivo da forca, barra e contador de 20 segundos por jogada, teclado virtual clicável, suporte ao teclado físico e placar.
- `hangman_engine.py`: Banco das 100 palavras (`DEFAULT_WORDS`), lógica do jogo (`HangmanEngine`), contagem de timeouts (`record_timeout`) e normalização de letras.
- `test_hangman_engine.py`: Testes unitários do motor do jogo e validação das 100 palavras.

## Como executar

```powershell
python forca.py
```

## Como rodar os testes

```powershell
python -m unittest discover -v
```
