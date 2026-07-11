import { describe, expect, it } from "vitest";

import { comunicadoBlockTypeLabel } from "./comunicadoBlockLabels";

describe("comunicadoBlockTypeLabel", () => {
  it("traduz chart_view e table_view para o gestor", () => {
    expect(comunicadoBlockTypeLabel("chart_view")).toBe("Gráfico");
    expect(comunicadoBlockTypeLabel("table_view")).toBe("Tabela");
    expect(comunicadoBlockTypeLabel("data_source")).toBe("Fonte de dados");
  });
});
