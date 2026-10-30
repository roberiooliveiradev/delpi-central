import { describe, expect, it } from "vitest";

import {
  buildNcHeroHighlights,
  buildNcProductsSummary,
  describeNcProduct,
  formatNcHistoryChange,
  formatNcHistoryValue,
  ncHistoryActorLabel,
  ncHistoryChangeLines,
} from "./ncPresentation";
import type { NcHistoryEvent } from "./types";

describe("describeNcProduct", () => {
  it("combina código e descrição quando disponíveis", () => {
    expect(
      describeNcProduct({
        product_code: "ABC123",
        product_description: "Transformador 75kVA",
      }),
    ).toBe("ABC123 — Transformador 75kVA");
  });

  it("mostra só o código quando a descrição está ausente", () => {
    expect(
      describeNcProduct({ product_code: "ABC123", product_description: null }),
    ).toBe("ABC123");
    expect(
      describeNcProduct({ product_code: "ABC123", product_description: "  " }),
    ).toBe("ABC123");
  });
});

describe("formatNcHistoryValue", () => {
  it("usa travessão para vazio/null", () => {
    expect(formatNcHistoryValue("customer_name", null)).toBe("—");
    expect(formatNcHistoryValue("customer_name", undefined)).toBe("—");
    expect(formatNcHistoryValue("customer_name", "")).toBe("—");
  });

  it("formata produtos por código e descrição — nunca [object Object]", () => {
    const products = [
      { product_code: "P1", product_description: "Trafo" },
      { product_code: "P2", product_description: null },
    ];
    const out = formatNcHistoryValue("products", products);
    expect(out).toBe("P1 — Trafo; P2");
    expect(out).not.toContain("[object Object]");
    expect(out).not.toContain("{");
  });

  it("formata tags como lista legível", () => {
    expect(formatNcHistoryValue("problem_tags", ["ruído", "vibração"])).toBe(
      "ruído; vibração",
    );
  });

  it("formata campos de data e data-hora conhecidos", () => {
    expect(formatNcHistoryValue("occurrence_date", "2026-10-27")).toBe(
      "27/10/2026",
    );
    const dt = formatNcHistoryValue("registered_at", "2026-10-27T12:30:00Z");
    expect(dt).not.toBe("2026-10-27T12:30:00Z");
    expect(dt).not.toBe("—");
  });

  it("serializa objetos genéricos como pares legíveis, sem JSON bruto", () => {
    const out = formatNcHistoryValue("custom", { a: 1, b: "x" });
    expect(out).toBe("a: 1; b: x");
    expect(out).not.toContain("[object Object]");
  });

  it("limita profundidade de objetos aninhados", () => {
    const deep = { a: { b: { c: { d: 1 } } } };
    const out = formatNcHistoryValue("custom", deep);
    expect(out).not.toContain("[object Object]");
  });
});

describe("ncHistoryChangeLines / actor", () => {
  const event: NcHistoryEvent = {
    id: "h1",
    nonconformity_id: "nc1",
    event_type: "updated",
    actor_user_id: "u-1",
    actor_email: "ana@delpi.com.br",
    actor_name: "Ana Silva",
    created_at: "2026-10-28T10:00:00Z",
    changes: {
      fields: [
        {
          field: "products",
          label: "Produtos",
          old: null,
          new: [{ product_code: "P1", product_description: "Trafo" }],
        },
        {
          field: "status",
          label: "Status",
          old: "open",
          new: "in_progress",
        },
      ],
    },
  };

  it("gera linhas legíveis old → new sem [object Object]", () => {
    const lines = ncHistoryChangeLines(event);
    expect(lines).toHaveLength(2);
    expect(lines[0]).toBe("Produtos: — → P1 — Trafo");
    expect(lines[1]).toBe("Status: open → in_progress");
    expect(lines.join(" ")).not.toContain("[object Object]");
  });

  it("prefere actor_name e degrada para e-mail/usuário genérico", () => {
    expect(ncHistoryActorLabel(event)).toBe("Ana Silva");
    expect(ncHistoryActorLabel({ ...event, actor_name: null })).toBe(
      "ana@delpi.com.br",
    );
    expect(
      ncHistoryActorLabel({ ...event, actor_name: null, actor_email: null }),
    ).toBe("Usuário do Portal");
  });

  it("formatNcHistoryChange cobre o rótulo oficial do contrato", () => {
    expect(
      formatNcHistoryChange({
        field: "defect_description",
        label: "Descrição do problema",
        old: "x",
        new: "y",
      }),
    ).toBe("Descrição do problema: x → y");
  });
});

describe("buildNcHeroHighlights", () => {
  const indicators = {
    current_days_without_nc: 12,
    record_days_without_nc: 45,
    last_nc_date: "2026-10-15",
    reference_start_date: "2020-01-01",
    as_of_date: "2026-10-27",
    nc_count: 53,
  };

  it("integra os valores oficiais da API no hero", () => {
    const highlights = buildNcHeroHighlights(indicators);
    expect(highlights).toHaveLength(2);
    expect(highlights[0].id).toBe("days-without-nc");
    expect(highlights[0].value).toBe("12");
    expect(highlights[0].description).toContain("15/10/2026");
    expect(highlights[1].id).toBe("record-days-without-nc");
    expect(highlights[1].value).toBe("45");
    expect(highlights[1].description).toContain("53");
  });

  it("mostra estado honesto sem NC registrada", () => {
    const highlights = buildNcHeroHighlights({
      ...indicators,
      last_nc_date: null,
      nc_count: 0,
    });
    expect(highlights[0].description).toBe("Sem ocorrências registradas");
  });

  it("usa placeholder de loading até o fetch — nunca recalcula", () => {
    const highlights = buildNcHeroHighlights(null);
    expect(highlights.every((h) => h.loading)).toBe(true);
    expect(highlights.every((h) => h.value === "…")).toBe(true);
  });
});

describe("buildNcProductsSummary", () => {
  const products = [
    { product_code: "P1", product_description: "Um" },
    { product_code: "P2", product_description: "Dois" },
    { product_code: "P3", product_description: null },
  ];

  it("mostra os primeiros itens e conta o excedente", () => {
    const summary = buildNcProductsSummary(products);
    expect(summary.visible).toHaveLength(2);
    expect(summary.overflowCount).toBe(1);
    expect(summary.fullLabel).toBe("P1 — Um; P2 — Dois; P3");
  });

  it("respeita maxVisible e aceita lista vazia", () => {
    expect(buildNcProductsSummary(products, 3).overflowCount).toBe(0);
    const empty = buildNcProductsSummary([]);
    expect(empty.visible).toHaveLength(0);
    expect(empty.fullLabel).toBe("");
  });
});
