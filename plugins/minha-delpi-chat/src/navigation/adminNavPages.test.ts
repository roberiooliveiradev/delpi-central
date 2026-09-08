import { describe, expect, it } from "vitest";

import { defaultPageForSubTab, nestedPageFromSlug, nestedPageSlug } from "./adminNavPages";

describe("adminNavPages", () => {
  it("resolve slug canônico EN e alias PT de aprendizagem", () => {
    expect(nestedPageSlug("learning", "finetuning")).toBe("fine-tuning");
    expect(nestedPageFromSlug("learning", "fine-tuning")).toBe("finetuning");
    expect(nestedPageFromSlug("learning", "ajuste-fino")).toBe("finetuning");
    expect(defaultPageForSubTab("learning")).toBe("pipeline");
  });

  it("resolve páginas aninhadas de métricas (Observe) EN + PT", () => {
    expect(defaultPageForSubTab("metrics")).toBe("overview");
    expect(nestedPageSlug("metrics", "overview")).toBe("overview");
    expect(nestedPageFromSlug("metrics", "overview")).toBe("overview");
    expect(nestedPageFromSlug("metrics", "visao-geral")).toBe("overview");
    expect(nestedPageFromSlug("metrics", "cost")).toBe("cost");
    expect(nestedPageFromSlug("metrics", "custo")).toBe("cost");
    expect(nestedPageFromSlug("metrics", "sql")).toBe("sql");
  });
});
