import { describe, expect, it } from "vitest";

import {
  normalizeOpportunityKey,
  pickBestProposalDocumentForOpportunity,
  scoreProposalDocumentForOpportunity,
} from "./resolveProposalDocumentForOpportunity";
import type { ProposalDocumentListItem } from "../types/proposalsDocument";

function item(
  partial: Partial<ProposalDocumentListItem> & Pick<ProposalDocumentListItem, "proposta_interna">,
): ProposalDocumentListItem {
  return {
    numero_ov: "",
    oportunidade: "",
    versao: "1",
    data: null,
    cliente: "",
    filial: "01",
    quantidade_itens: 0,
    ...partial,
  };
}

describe("resolveProposalDocumentForOpportunity helpers", () => {
  it("normaliza chave de OV", () => {
    expect(normalizeOpportunityKey(" 00123 ")).toBe("123");
    expect(normalizeOpportunityKey("ady-9")).toBe("ADY-9");
  });

  it("escolhe melhor match por score e data", () => {
    const items = [
      item({
        proposta_interna: "A",
        numero_ov: "100",
        data: "2024-01-01",
        versao: "1",
      }),
      item({
        proposta_interna: "B",
        numero_ov: "100",
        data: "2025-06-01",
        versao: "2",
      }),
      item({
        proposta_interna: "C",
        oportunidade: "999",
        data: "2026-01-01",
      }),
    ];
    expect(pickBestProposalDocumentForOpportunity(items, "100")?.proposta_interna).toBe(
      "B",
    );
    expect(scoreProposalDocumentForOpportunity(items[2]!, "100")).toBe(0);
  });
});
