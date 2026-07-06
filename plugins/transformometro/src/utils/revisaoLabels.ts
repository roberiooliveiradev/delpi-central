import { cenarioLabel } from "../content/cenarioLabels";
import type { Revisao } from "../data/api/transformometroApi";

type RevisaoLike = Pick<Revisao, "versao_revisao" | "cenario_tipo">;

export function revisaoDisplayLabel(revisao: RevisaoLike): string {
  const versao = revisao.versao_revisao?.trim() || "?";
  return `v${versao} · ${cenarioLabel(revisao.cenario_tipo)}`;
}

export function revisaoShortLabel(revisao: RevisaoLike): string {
  return `v${revisao.versao_revisao?.trim() || "?"}`;
}
