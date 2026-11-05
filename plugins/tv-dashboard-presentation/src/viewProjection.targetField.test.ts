import { describe, expect, it } from "vitest";

import {
  parseComunicadoConfig,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";
import { normalizeKpiProjection } from "./viewProjection";
import { resolveKpiViewPresentation } from "./resolveKpiPresentation";

describe("normalizeKpiProjection — targetField / meta dinâmica", () => {
  it("preserva target, targetField, comparisonMode e higherIsBetter", () => {
    const next = normalizeKpiProjection({
      metrics: [
        {
          field: "realizado",
          target: 85,
          targetField: " meta ",
          targetAggregation: "avg",
          comparisonMode: "target",
          higherIsBetter: false,
          colorRules: [{ op: "lte", compareField: "meta", value: 0, tone: "positive" }],
        },
      ],
    });
    expect(next?.metrics?.[0]).toMatchObject({
      field: "realizado",
      target: 85,
      targetField: "meta",
      targetAggregation: "avg",
      comparisonMode: "target",
      higherIsBetter: false,
    });
    expect(next?.metrics?.[0]?.colorRules?.[0]?.compareField).toBe("meta");
  });

  it("omite targetField vazio e target não finito", () => {
    const next = normalizeKpiProjection({
      metrics: [{ field: "a", targetField: "  ", target: Number.NaN }],
    });
    expect(next?.metrics?.[0]?.targetField).toBeUndefined();
    expect(next?.metrics?.[0]?.target).toBeUndefined();
  });
});

describe("MDD / nativeConfig — bindings round-trip (H)", () => {
  it("preserva targetField/titleField/compareField e não persiste displays resolvidos", () => {
    const serialized = serializeComunicadoConfig({
      version: 1,
      blocks: [
        {
          id: "kpi-1",
          type: "kpi_view",
          frame: { x: 0, y: 0, w: 20, h: 20 },
          kpiOptions: {
            targetField: "meta",
            titleField: "titulo",
            subtitleField: "sub",
            colorRules: [{ op: "lte", compareField: "meta", value: 0, tone: "positive" }],
          },
          kpiProjection: {
            metrics: [{ field: "realizado", targetField: "meta", targetAggregation: "first" }],
          },
          resolved: {
            kpiPresentation: {
              titleDisplay: "NÃO DEVE PERSISTIR",
              targetValue: 99,
              resolvedColorRules: [{ op: "lte", value: 5, tone: "positive" }],
            },
          },
        } as never,
      ],
    });
    const parsed = parseComunicadoConfig(serialized);
    const block = parsed?.blocks?.[0] as {
      kpiOptions?: { targetField?: string; titleField?: string; colorRules?: Array<{ compareField?: string }> };
      kpiProjection?: { metrics?: Array<{ targetField?: string }> };
      resolved?: unknown;
    };
    expect(block.kpiOptions?.targetField).toBe("meta");
    expect(block.kpiOptions?.titleField).toBe("titulo");
    expect(block.kpiOptions?.colorRules?.[0]?.compareField).toBe("meta");
    expect(block.kpiProjection?.metrics?.[0]?.targetField).toBe("meta");
    expect(block.resolved).toBeUndefined();
  });
});

describe("resolveKpiViewPresentation — displays dinâmicos (I parity paint)", () => {
  it("usa titleDisplay/subtitleDisplay/resolvedColorRules do enrich", () => {
    const presentation = resolveKpiViewPresentation(
      {
        kpi: { value: 3, label: "legado", displayValue: "3" },
        kpiPresentation: {
          valueDisplay: "3",
          titleDisplay: "Retrabalho",
          subtitleDisplay: "Linha 2",
          resolvedColorRules: [{ op: "lte", value: 5, tone: "positive" }],
          showComparison: false,
        },
      },
      {
        title: "Ignorado quando titleDisplay existe",
        subtitle: "Ignorado",
        colorRules: [{ op: "lte", value: 999, tone: "negative" }],
        tone: "default",
      },
    );
    expect(presentation.label).toBe("Retrabalho");
    expect(presentation.hint).toBe("Linha 2");
    expect(presentation.tone).toBe("positive");
  });

  it("expõe targetDisplay do enrich sem recalcular a meta", () => {
    const presentation = resolveKpiViewPresentation({
      kpi: { value: 93.7, displayValue: "93,70%" },
      kpiPresentation: {
        valueDisplay: "93,70%",
        targetDisplay: "85,00%",
        targetValue: 85,
        showComparison: true,
        comparisonDisplay: "▲ +8,70 p.p. vs meta",
      },
    });
    expect(presentation.targetText).toBe("85,00%");
    expect(presentation.valueText).toBe("93,70%");
  });
});
