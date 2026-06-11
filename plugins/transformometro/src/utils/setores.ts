import type { SetorOption } from "../data/api/transformometroApi";

export function filterSetoresByFilial(
  setores: SetorOption[],
  filialId: string
): SetorOption[] {
  if (!filialId) return setores;
  return setores.filter((setor) => setor.filiais.includes(filialId));
}

export function setorLabel(setores: SetorOption[] | undefined, setorId: string): string {
  if (!setorId) return "—";
  return setores?.find((setor) => setor.id === setorId)?.label ?? setorId;
}

export function resolveSetorIdForFilial(
  setores: SetorOption[],
  filialId: string,
  currentSetorId: string
): string {
  const available = filterSetoresByFilial(setores, filialId);
  if (available.some((setor) => setor.id === currentSetorId)) {
    return currentSetorId;
  }
  return available[0]?.id ?? currentSetorId;
}
