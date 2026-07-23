import { describe, expect, it } from "vitest";

import {
  buildFieldLabelsFromTableColumns,
  formatChartAxisValue,
  resolveFieldLabel,
} from "./presentationFieldLabels";

describe("presentationFieldLabels", () => {
  it("usa vocabulário configurado quando disponível", () => {
    expect(
      resolveFieldLabel("ordered_quantity", {
        ordered_quantity: "Qtd. pedida",
      }),
    ).toBe("Qtd. pedida");
  });

  it("formata datas compactas no eixo do gráfico", () => {
    expect(
      formatChartAxisValue("20260317", "issue_date", {
        issue_date: "date",
      }),
    ).toBe("17/03/2026");
  });

  it("preserva datas já em dd/mm/yyyy no eixo do gráfico", () => {
    expect(
      formatChartAxisValue("23/07/2026", "start_date", {
        start_date: "date",
      }),
    ).toBe("23/07/2026");
  });

  it("reaproveita labels da tabela ao montar gráfico", () => {
    const { fieldLabels, fieldFormats } = buildFieldLabelsFromTableColumns([
      { key: "issue_date", label: "Data emissão", dataType: "date" },
      { key: "ordered_quantity", label: "Qtd. pedida", dataType: "quantity" },
    ]);

    expect(fieldLabels.ordered_quantity).toBe("Qtd. pedida");
    expect(fieldFormats.issue_date).toBe("date");
  });

  it("prefere label da API em vez de humanize legacy", () => {
    const { fieldLabels } = buildFieldLabelsFromTableColumns([
      { key: "simulated_unit_cost", label: "Custo unitário simulado" },
    ]);

    expect(resolveFieldLabel("simulated_unit_cost", fieldLabels)).toBe(
      "Custo unitário simulado",
    );
  });

  it("usa humanize legacy só sem vocabulário configurado", () => {
    expect(resolveFieldLabel("raw_material_code")).toBe("Raw Material Code");
  });
});
