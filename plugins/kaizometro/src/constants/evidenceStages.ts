import type { KaizenEvidenceStage } from "../types/kaizen";

export const EVIDENCE_STAGE_OPTIONS: Array<{ value: KaizenEvidenceStage; label: string }> = [
  { value: "antes", label: "Antes" },
  { value: "depois", label: "Depois" },
  { value: "geral", label: "Geral" },
];

export const EVIDENCE_STAGE_LABELS: Record<KaizenEvidenceStage, string> = Object.fromEntries(
  EVIDENCE_STAGE_OPTIONS.map((item) => [item.value, item.label]),
) as Record<KaizenEvidenceStage, string>;

/** Rótulos de coluna na galeria (ex.: «Gerais» no plural). */
export const EVIDENCE_STAGE_GALLERY_LABELS: Record<KaizenEvidenceStage, string> = {
  ...EVIDENCE_STAGE_LABELS,
  geral: "Gerais",
};
