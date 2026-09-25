import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";
import { MousePointer2 } from "lucide-react";

import {
  applyFormatElementRibbonTabMeta,
  resolveFormatElementTabLabel,
} from "./applyFormatElementRibbonTabMeta";

describe("applyFormatElementRibbonTabMeta", () => {
  it("mapeia tipos para Formatar*", () => {
    expect(resolveFormatElementTabLabel({ type: "text" } as ComunicadoBlock)).toBe(
      "Formatar Texto",
    );
    expect(resolveFormatElementTabLabel({ type: "shape" } as ComunicadoBlock)).toBe(
      "Formatar Forma",
    );
    expect(resolveFormatElementTabLabel({ type: "chart_view" } as ComunicadoBlock)).toBe(
      "Formatar Gráfico",
    );
    expect(resolveFormatElementTabLabel({ type: "kpi_view" } as ComunicadoBlock)).toBe(
      "Formatar KPI",
    );
    expect(resolveFormatElementTabLabel({ type: "image" } as ComunicadoBlock)).toBe(
      "Formatar Imagem",
    );
  });

  it("renomeia só a aba element", () => {
    const tabs = applyFormatElementRibbonTabMeta(
      [
        {
          id: "element" as const,
          label: "Elemento",
          hint: "h",
          icon: MousePointer2,
        },
        {
          id: "data" as const,
          label: "Dados",
          hint: "h",
          icon: MousePointer2,
        },
      ],
      { type: "heading" } as ComunicadoBlock,
    );
    expect(tabs.find((t) => t.id === "element")?.label).toBe("Formatar Texto");
    expect(tabs.find((t) => t.id === "data")?.label).toBe("Dados");
  });
});
