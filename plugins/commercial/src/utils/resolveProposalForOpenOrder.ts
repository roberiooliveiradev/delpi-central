import { getCommercialProposals } from "../api/analyticsApi";
import type { CommercialProposal } from "../types/analytics";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";

export type ResolvedProposalLink = {
  proposalNumber: string;
  branch: string | null;
};

function normalizeCode(value: string | null | undefined): string {
  return String(value || "")
    .trim()
    .replace(/^0+/, "")
    .toUpperCase();
}

/** Score de match OV↔linha CM (filial+cliente; número OV=pedido é bônus forte). */
export function scoreProposal(
  proposal: CommercialProposal,
  item: OpenOrdersTotvsItem,
): number {
  let score = 0;
  const pedido = item.pedido.trim();
  if (proposal.proposal_number.trim() === pedido) score += 100;

  const branch = item.filial.trim();
  if (branch && proposal.branch.trim() === branch) score += 40;

  const customer = normalizeCode(item.codigo_cadastro);
  const store = normalizeCode(item.loja_cadastro);
  if (customer && normalizeCode(proposal.customer_code) === customer) score += 30;
  if (store && normalizeCode(proposal.customer_store) === store) score += 10;

  if (proposal.status_category === "open") score += 5;
  if (proposal.status_category === "won") score += 2;

  return score;
}

/**
 * Resolve OV (AD1_NROPOR) a partir do pedido SC5 quando a lista CM
 * não trouxe `proposal_number`. Usa busca em /commercial/proposals — não
 * trata C5_NUM como path de OV.
 */
export async function resolveProposalForOpenOrderLine(
  item: OpenOrdersTotvsItem,
  signal?: AbortSignal,
): Promise<ResolvedProposalLink | null> {
  const explicit = item.proposal_number?.trim();
  if (explicit) {
    return { proposalNumber: explicit, branch: item.filial?.trim() || null };
  }

  const pedido = item.pedido?.trim();
  if (!pedido) return null;

  const branch = item.filial?.trim() || undefined;
  try {
    const page = await getCommercialProposals(
      {
        search: pedido,
        branch,
        page: 1,
        page_size: 20,
      },
      signal,
    );
    const items = page.items ?? [];
    if (items.length === 0) return null;

    const ranked = [...items]
      .map((proposal) => ({ proposal, score: scoreProposal(proposal, item) }))
      .filter((row) => row.score >= 40)
      .sort((a, b) => b.score - a.score);

    const best = ranked[0]?.proposal;
    if (!best?.proposal_number?.trim()) return null;

    return {
      proposalNumber: best.proposal_number.trim(),
      branch: best.branch?.trim() || branch || null,
    };
  } catch {
    return null;
  }
}
