import { ChessEngine, chooseAIMove } from './chess_engine.js';

self.onmessage = (event) => {
  const { requestId, moves, difficulty, useBook } = event.data;
  const engine = ChessEngine.fromMoves(moves);
  const move = chooseAIMove(engine, difficulty, Math.random, { useBook });
  self.postMessage({ requestId, move });
};
