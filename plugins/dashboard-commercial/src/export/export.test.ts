import { describe, expect, it } from "vitest";

import {
  buildDashboardKpisPayload,
  buildFunnelPayload,
  buildHistoryPayload,
  buildProposalsPayload,
} from "./commercialExportBuilders";
import { csvCell, sanitizeFilename, sanitizeSheetName } from "./primitives";
import { buildProductStructuresPayload } from "./productStructureExport";

describe("export primitives", () => {
  it("escapa células CSV com separador", () => {
    expect(csvCell("a;b")).toBe('"a;b"');
  });

  it("sanitiza nome de arquivo", () => {
    expect(sanitizeFilename("Dashboard / Comercial")).toBe("Dashboard_Comercial");
  });

  it("limita nome de aba Excel", () => {
    expect(sanitizeSheetName("Nome muito longo para planilha Excel")).toHaveLength(31);
  });
});

describe("commercial export builders", () => {
  it("monta payload de indicadores", () => {
    const payload = buildDashboardKpisPayload([
      { indicador: "ROL", valor: "R$ 1", contexto: "Período" },
    ]);

    expect(payload.columns).toHaveLength(3);
    expect(payload.rows).toHaveLength(1);
  });

  it("monta payload de propostas", () => {
    const payload = buildProposalsPayload([
      {
        branch: "01",
        proposal_number: "123",
        revision: "001",
        description: "Teste",
        proposal_date: "20260101",
        end_date: null,
        status_label: "Aberta",
      },
    ]);

    expect(payload.rows[0]?.proposal_number).toBe("123");
  });

  it("monta payload do funil", () => {
    const payload = buildFunnelPayload({
      qtd_proposals: 10,
      qtd_won: 4,
      sales_conversion_rate_pct: 40,
    });

    expect(payload.rows).toHaveLength(3);
  });

  it("inclui colunas de fluxo no histórico", () => {
    const payload = buildHistoryPayload([
      {
        revision: "001",
        process_code: "01",
        stage_code: "10",
        flow_transition_labels: ["Entrada na engenharia"],
        is_current: true,
        is_open: true,
      },
    ]);

    expect(payload.columns.some((column) => column.key === "flow")).toBe(true);
    expect(payload.rows[0]?.flow).toContain("engenharia");
  });

  it("achata BOM para exportação tabular", () => {
    const payload = buildProductStructuresPayload([
      {
        product: { code: "PI-001", description: "Produto teste" },
        structure: {
          root: {
            code: "PI-001",
            description: "Raiz",
            type: "PI",
            quantity: 1,
            components: [
              {
                code: "MP-001",
                description: "Componente",
                type: "MP",
                quantity: 2,
              },
            ],
          },
        },
      },
    ]);

    expect(payload.rows.length).toBeGreaterThanOrEqual(2);
    expect(payload.rows.some((row) => row.code === "MP-001")).toBe(true);
  });
});
