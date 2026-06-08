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

  it("reaproveita labels da tabela ao montar gráfico", () => {
    const { fieldLabels, fieldFormats } = buildFieldLabelsFromTableColumns([
      { key: "issue_date", label: "Data emissão", dataType: "date" },
      { key: "ordered_quantity", label: "Qtd. pedida", dataType: "quantity" },
    ]);

    expect(fieldLabels.ordered_quantity).toBe("Qtd. pedida");
    expect(fieldFormats.issue_date).toBe("date");
  });
});
