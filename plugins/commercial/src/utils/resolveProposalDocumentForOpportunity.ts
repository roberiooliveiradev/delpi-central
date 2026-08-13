import { listProposalsDocuments } from "../api/commercialProposalsApi";
import type { ProposalDocumentListItem } from "../types/proposalsDocument";

/** Normaliza OV / oportunidade para match (trim, sem zeros à esquerda, uppercase). */
export function normalizeOpportunityKey(value: string | null | undefined): string {
  const raw = (value ?? "").trim().toUpperCase();
  if (!raw) return "";
  const stripped = raw.replace(/^0+(?=\d)/, "");
  return stripped || raw;
}

function parseSortableDate(value: string | null | undefined): number {
  if (!value) return 0;
  const t = Date.parse(value);
  return Number.isFinite(t) ? t : 0;
}

function parseVersionScore(value: string | null | undefined): number {
  const digits = (value ?? "").replace(/[^\d]/g, "");
  if (!digits) return 0;
  const n = Number(digits);
  return Number.isFinite(n) ? n : 0;
}

export function scoreProposalDocumentForOpportunity(
  item: ProposalDocumentListItem,
  opportunityKey: string,
): number {
  const key = normalizeOpportunityKey(opportunityKey);
  if (!key) return 0;
  const ov = normalizeOpportunityKey(item.numero_ov);
  const opp = normalizeOpportunityKey(item.oportunidade);
  let score = 0;
  if (ov && ov === key) score += 100;
  else if (ov && (ov.includes(key) || key.includes(ov))) score += 40;
  if (opp && opp === key) score += 80;
  else if (opp && (opp.includes(key) || key.includes(opp))) score += 30;
  if (score === 0) return 0;
  return score;
}

export function pickBestProposalDocumentForOpportunity(
  items: readonly ProposalDocumentListItem[],
  opportunityKey: string,
): ProposalDocumentListItem | null {
  const key = normalizeOpportunityKey(opportunityKey);
  if (!key) return null;
  let best: ProposalDocumentListItem | null = null;
  let bestScore = 0;
  for (const item of items) {
    const score = scoreProposalDocumentForOpportunity(item, key);
    if (score <= 0) continue;
    if (!best || score > bestScore) {
      best = item;
      bestScore = score;
      continue;
    }
    if (score < bestScore) continue;
    const dateDelta =
      parseSortableDate(item.data) - parseSortableDate(best.data);
    if (dateDelta > 0) {
      best = item;
      continue;
    }
    if (
      dateDelta === 0 &&
      parseVersionScore(item.versao) > parseVersionScore(best.versao)
    ) {
      best = item;
    }
  }
  return best;
}

export type ResolveProposalDocumentResult =
  | { status: "none" }
  | { status: "matched"; item: ProposalDocumentListItem; matchCount: number };

/**
 * Lista ADY e resolve documento pela OV (numero_ov / oportunidade).
 * 0 → none; 1+ → melhor score (data/versão).
 */
export async function resolveProposalDocumentForOpportunity(
  opportunityNumber: string,
  options?: { limit?: number; signal?: AbortSignal },
): Promise<ResolveProposalDocumentResult> {
  const key = normalizeOpportunityKey(opportunityNumber);
  if (!key) return { status: "none" };
  const data = await listProposalsDocuments(options?.limit ?? 200, options?.signal);
  const matches = (data.items ?? []).filter(
    (item) => scoreProposalDocumentForOpportunity(item, key) > 0,
  );
  if (matches.length === 0) return { status: "none" };
  const best = pickBestProposalDocumentForOpportunity(matches, key);
  if (!best) return { status: "none" };
  return { status: "matched", item: best, matchCount: matches.length };
}
