import { describe, expect, it } from "vitest";

import {
  mapSuggestItemToMentionHit,
  mapSuggestItemsToMentionHits,
  mentionHitToPayload,
  mentionsPresentInBody,
} from "./mentionSuggestAdapter";

describe("mentionSuggestAdapter", () => {
  it("mapeia DTO da API para hit do MentionMenu com groupLabel", () => {
    const hit = mapSuggestItemToMentionHit(
      {
        kind: "user",
        label: "Ana Silva",
        subtitle: "ana@delpi.com",
        ref: { user_id: "u1" },
      },
      0,
    );
    expect(hit.id).toContain("user:");
    expect(hit.kind).toBe("user");
    expect(hit.label).toBe("Ana Silva");
    expect(hit.subtitle).toBe("ana@delpi.com");
    expect(hit.groupLabel).toBe("Pessoas");
    expect(hit.ref).toEqual({ user_id: "u1" });
  });

  it("preserva id estável quando a API envia id", () => {
    const hit = mapSuggestItemToMentionHit({
      id: "hit-9",
      kind: "order",
      label: "102942",
      ref: { branch: "01", order: "102942" },
    });
    expect(hit.id).toBe("hit-9");
    expect(hit.groupLabel).toBe("Pedidos");
  });

  it("filtra mentions presentes no corpo", () => {
    const pending = mapSuggestItemsToMentionHits([
      { kind: "user", label: "Ana Silva", ref: { user_id: "u1" } },
      { kind: "order", label: "102942", ref: { order: "102942" } },
    ]).map(mentionHitToPayload);

    const kept = mentionsPresentInBody(
      "Oi @Ana Silva sobre o pedido 999",
      pending,
    );
    expect(kept).toHaveLength(1);
    expect(kept[0]?.kind).toBe("user");
  });
});
