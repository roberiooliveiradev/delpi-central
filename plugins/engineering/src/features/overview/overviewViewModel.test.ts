import { describe, expect, it } from "vitest";

import { buildOverviewCards } from "./overviewViewModel";
import type { OverviewIndicator, OverviewResponse } from "../../types/overview";

function indicator(over: Partial<OverviewIndicator>): OverviewIndicator {
  return {
    id: "lmp_on_time",
    label: "% LMP dentro do prazo",
    family: "lmp",
    availability: "available",
    value: 92.5,
    unit: "%",
    scope: "consolidado",
    start_date: "2026-10-01",
    end_date: "2026-10-28",
    source: "api-delpi",
    source_endpoint: "GET /engineering/lmps/dashboard/summary",
    ...over,
  };
}

function overview(indicators: OverviewIndicator[]): OverviewResponse {
  return {
    schema_version: "1.0",
    generated_at: "2026-10-28T12:00:00Z",
    status: "available",
    filters: {},
    indicators,
  };
}

describe("buildOverviewCards — paridade com Dashboard Engenharia", () => {
  it("formata % LMP com sufixo do owner", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          value: 92.5,
          value_suffix: "%",
          value_decimals: 1,
        }),
      ]),
    );
    expect(card.value).toBe("92,5%");
    expect(card.contextLabel).toContain("Consolidado");
    expect(card.contextLabel).toContain("01/10/2026");
  });

  it("formata lead time com decimais do owner", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          id: "lmp_lead_time",
          label: "Lead time médio",
          value: 7.3,
          unit: "dias úteis",
          value_decimals: 2,
        }),
      ]),
    );
    expect(card.value).toBe("7,30");
  });

  it("formata total de propostas como inteiro pt-BR", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          id: "lmp_total_proposals",
          label: "Total de propostas",
          value: 1234,
          unit: "propostas",
        }),
      ]),
    );
    expect(card.value).toBe("1.234");
  });

  it("formata ganhos TRANSFORMA+ com prefixo do owner", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          id: "transforma_gross_savings",
          label: "Ganhos brutos TRANSFORMA+",
          family: "transforma",
          value: 12500.5,
          unit: "BRL",
          value_prefix: "R$ ",
          value_decimals: 2,
        }),
      ]),
    );
    expect(card.value).toBe("R$  12.500,50".replace("  ", " "));
  });

  it("formata ROI em multiplicador ×", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          id: "transforma_roi",
          label: "ROI médio TRANSFORMA+",
          family: "transforma",
          value: 3.42,
          unit: "x",
        }),
      ]),
    );
    expect(card.value).toBe("3,4×");
  });

  it("repassa meta e IDD sem recálculo", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          has_goal: true,
          goal_label: "Meta oficial",
          goal_value: 90,
          value_suffix: "%",
          value_decimals: 1,
          idd: 94,
          idd_label: "engineering-projects-on-time",
        }),
      ]),
    );
    expect(card.goalLabel).toBe("Meta oficial");
    expect(card.iddScoreLabel).toBe("94,00");
  });

  it("sem goal_label do owner, formata a meta numérica", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          has_goal: true,
          goal_value: 90,
          comparable_goal: 90,
          value_suffix: "%",
          value_decimals: 1,
        }),
      ]),
    );
    expect(card.goalLabel).toBe("90,0%");
  });

  it("operacionais nunca apresentam meta/IDD/badges (OVERVIEW.R1)", () => {
    // Mesmo que o contrato vaze metadados estratégicos do grupo para
    // soluções/ROI, o view model ignora — elegibilidade é por
    // indicador canônico, não por família.
    const operational = [
      "lmp_lead_time",
      "lmp_total_proposals",
      "transforma_solutions",
      "transforma_roi",
    ];
    const cards = buildOverviewCards(
      overview(
        operational.map((id) =>
          indicator({
            id,
            family: id.startsWith("lmp") ? "lmp" : "transforma",
            has_goal: true,
            goal_value: 10000,
            goal_label: "Vazado",
            comparable_goal: 10000,
            reference_goal: 9000,
            goal_scope_label: "Consolidado",
            performance_direction: "higher_is_better",
            idd: 99,
            idd_label: "vazado",
          }),
        ),
      ),
    );
    for (const card of cards) {
      expect(card.goalLabel).toBeUndefined();
      expect(card.goalPrefix).toBeUndefined();
      expect(card.monthlyGoalLabel).toBeUndefined();
      expect(card.goalScopeBadge).toBeUndefined();
      expect(card.goalPerformanceBadge).toBeUndefined();
      expect(card.iddScoreLabel).toBeUndefined();
      expect(card.availability).toBe("available");
    }
    // Mas os elegíveis continuam apresentando meta/IDD.
    const [strategic] = buildOverviewCards(
      overview([
        indicator({
          id: "transforma_gross_savings",
          family: "transforma",
          has_goal: true,
          goal_value: 10000,
          idd: 81,
        }),
      ]),
    );
    expect(strategic.goalLabel).toBeDefined();
    expect(strategic.iddScoreLabel).toBe("81,00");
  });

  it("escopo por unidade rotula a unidade, não 'Consolidado'", () => {
    const [card] = buildOverviewCards(
      overview([indicator({ scope: "01" })]),
    );
    expect(card.contextLabel).toContain("Santa Catarina");
    expect(card.contextLabel).not.toContain("Consolidado");
  });
});

describe("estados honestos", () => {
  it("indicador unavailable não mostra valor nem zero", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          availability: "unavailable",
          value: null,
          reason: "timeout",
        }),
      ]),
    );
    expect(card.availability).toBe("unavailable");
    expect(card.value).toBe("—");
    expect(card.stateMessage).toContain("indisponível");
  });

  it("indicador forbidden preserva mensagem do owner", () => {
    const [card] = buildOverviewCards(
      overview([
        indicator({
          availability: "forbidden",
          value: null,
          message: "Acesso negado pelo owner da fonte.",
        }),
      ]),
    );
    expect(card.availability).toBe("forbidden");
    expect(card.stateMessage).toBe("Acesso negado pelo owner da fonte.");
  });

  it("indicador empty exibe mensagem de ausência oficial", () => {
    const [card] = buildOverviewCards(
      overview([indicator({ availability: "empty", value: null })]),
    );
    expect(card.availability).toBe("empty");
    expect(card.stateMessage).toContain("Sem dados oficiais");
  });

  it("value null oficial renderiza — sem inventar zero", () => {
    const [card] = buildOverviewCards(
      overview([indicator({ value: null })]),
    );
    expect(card.value).toBe("—");
  });
});
