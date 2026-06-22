import { describe, expect, it } from "vitest";

import {
  resolveIcebreakerCardPresentation,
  resolveIcebreakerVisualKind,
} from "./agentIcebreakers";

describe("resolveIcebreakerCardPresentation", () => {
  it("usa rótulo curto e hint — sem código 10080001 no subtítulo", () => {
    expect(
      resolveIcebreakerCardPresentation("me fale do produto {{productCode}}"),
    ).toEqual({
      title: "Consultar produto",
      subtitle: "Cadastro, estoque e visão geral",
    });
  });

  it("usa hint quando o template não tem placeholder", () => {
    expect(resolveIcebreakerCardPresentation("o que você pode fazer?")).toEqual({
      title: "Capacidades",
      subtitle: "Ferramentas, dados e limites do agente",
    });
  });

  it("rotula playbooks fabril, preço MP e impacto de custo", () => {
    expect(
      resolveIcebreakerCardPresentation(
        "qual o status fabril hoje do produto {{productCode}}?",
      ),
    ).toEqual({
      title: "Status fabril",
      subtitle: "Estrutura, MPs, produção e expedição",
    });

    expect(
      resolveIcebreakerCardPresentation("análise de preço da matéria-prima {{productCode}}"),
    ).toEqual({
      title: "Preço da MP",
      subtitle: "Fornecedor, ICMS, orçamento e variação",
    });

    expect(
      resolveIcebreakerCardPresentation(
        "quais materiais mais impactam o custo do PA {{productCode}}?",
      ),
    ).toEqual({
      title: "Impacto de custo",
      subtitle: "Ranking Pareto das MPs na BOM",
    });
  });

  it("aceita label e hint vindos do metadata da API", () => {
    expect(
      resolveIcebreakerCardPresentation("pergunta custom {{productCode}}", {
        label: "Título custom",
        hint: "Subtítulo configurável",
      }),
    ).toEqual({
      title: "Título custom",
      subtitle: "Subtítulo configurável",
    });
  });

  it("resolve variante visual por template", () => {
    expect(
      resolveIcebreakerVisualKind({
        template: "qual o estoque do produto {{productCode}}?",
        fields: [{ id: "productCode", label: "Código", fieldType: "productCode" }],
      }),
    ).toBe("stock");
    expect(
      resolveIcebreakerVisualKind({
        template: "pesquise na web sobre {{searchQuery}}",
        fields: [{ id: "searchQuery", label: "Termo", fieldType: "searchQuery" }],
      }),
    ).toBe("web");
  });
});
