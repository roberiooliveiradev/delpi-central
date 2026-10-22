/** Índices cíclicos do board (navegação manual e autoavanço). */
export function nextBoardIndex(current: number, length: number): number {
  if (length <= 0) return 0;
  return (current + 1) % length;
}

export function previousBoardIndex(current: number, length: number): number {
  if (length <= 0) return 0;
  return (current - 1 + length) % length;
}

/** Intervalo efetivo de rotação (mínimo 1s para TV / testes). */
export function rotationIntervalMs(rotationIntervalSec: number): number {
  return Math.max(1, rotationIntervalSec) * 1000;
}
