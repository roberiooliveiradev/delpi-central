import { describe, expect, it } from "vitest";

import {
  applyBranch,
  applyCompetence,
  applyDateEnd,
  applyDateStart,
  applyPreset,
  competenceToDateRange,
  dateRangeToCompetence,
  defaultFilters,
  readFiltersFromSearch,
  toApiFilters,
  type OverviewFilterState,
} from "./overviewFilters";

const NOW = new Date("2026-10-28T15:00:00-03:00");

const BASE: OverviewFilterState = {
  preset: "this_month",
  dateStart: "2026-10-01",
  dateEnd: "2026-10-28",
  competence: "2026-10",
  branch: "",
};

describe("defaultFilters", () => {
  it("usa o preset 'Este mês' como recorte padrão", () => {
    const state = defaultFilters(NOW);
    expect(state.preset).toBe("this_month");
    expect(state.dateStart).toBe("2026-10-01");
    expect(state.dateEnd).toBe("2026-10-28");
    expect(state.competence).toBe("2026-10");
    expect(state.branch).toBe("");
  });
});

describe("applyPreset", () => {
  it("'Hoje' resolve datas de hoje", () => {
    const next = applyPreset("today", BASE, NOW);
    expect(next.dateStart).toBe("2026-10-28");
    expect(next.dateEnd).toBe("2026-10-28");
  });

  it("'Mês passado' resolve o mês fechado", () => {
    const next = applyPreset("last_month", BASE, NOW);
    expect(next.dateStart).toBe("2026-09-01");
    expect(next.dateEnd).toBe("2026-09-30");
    expect(next.competence).toBe("2026-09");
  });

  it("'Personalizado' mantém datas atuais", () => {
    const next = applyPreset("custom", BASE, NOW);
    expect(next.preset).toBe("custom");
    expect(next.dateStart).toBe(BASE.dateStart);
    expect(next.dateEnd).toBe(BASE.dateEnd);
  });
});

describe("vínculo competência ↔ datas", () => {
  it("mudar competência atualiza o intervalo do mês", () => {
    const next = applyCompetence("2026-08", BASE, NOW);
    expect(next.dateStart).toBe("2026-08-01");
    expect(next.dateEnd).toBe("2026-08-31");
    expect(next.competence).toBe("2026-08");
  });

  it("competência do mês corrente termina em hoje", () => {
    const next = applyCompetence("2026-10", BASE, NOW);
    expect(next.dateEnd).toBe("2026-10-28");
  });

  it("datas no mesmo mês derivam competência", () => {
    const next = applyDateEnd("2026-10-15", {
      ...BASE,
      competence: "",
    }, NOW);
    expect(next.competence).toBe("2026-10");
    expect(next.preset).toBe("custom");
  });

  it("intervalo que cruza meses limpa a competência", () => {
    const next = applyDateStart("2026-09-15", BASE, NOW);
    expect(next.competence).toBe("");
  });
});

describe("competenceToDateRange / dateRangeToCompetence", () => {
  it("converte YYYY-MM em intervalo completo", () => {
    const range = competenceToDateRange("2026-02", "2026-10-28");
    expect(range).toEqual({
      dateStart: "2026-02-01",
      dateEnd: "2026-02-28",
    });
  });

  it("rejeita competência inválida", () => {
    expect(competenceToDateRange("2026-13", "2026-10-28")).toEqual({
      dateStart: "",
      dateEnd: "",
    });
  });

  it("deriva competência somente dentro do mesmo mês", () => {
    expect(dateRangeToCompetence("2026-10-05", "2026-10-20")).toBe(
      "2026-10",
    );
    expect(dateRangeToCompetence("2026-10-05", "2026-11-20")).toBe("");
  });
});

describe("toApiFilters", () => {
  it("serializa somente filtros válidos do contrato", () => {
    const api = toApiFilters({ ...BASE, branch: "01" });
    expect(api).toEqual({
      start_date: "2026-10-01",
      end_date: "2026-10-28",
      competence: "2026-10",
      branch: "01",
    });
  });

  it("descarta intervalo invertido sem inventar datas", () => {
    const api = toApiFilters({
      ...BASE,
      dateStart: "2026-10-31",
      dateEnd: "2026-10-01",
    });
    expect(api.start_date).toBeUndefined();
    expect(api.end_date).toBeUndefined();
  });

  it("descarta competência inválida", () => {
    const api = toApiFilters({ ...BASE, competence: "2026-13" });
    expect(api.competence).toBeUndefined();
  });
});

describe("unidade operacional", () => {
  it("branch vazio significa consolidado", () => {
    expect(toApiFilters(BASE).branch).toBeUndefined();
  });

  it("branch válido vai para a API", () => {
    const next = applyBranch("02", BASE);
    expect(toApiFilters(next).branch).toBe("02");
  });
});

describe("readFiltersFromSearch", () => {
  it("sem parâmetros retorna o padrão", () => {
    const state = readFiltersFromSearch("", NOW);
    expect(state.preset).toBe("this_month");
  });

  it("lê datas + competência + unidade da URL", () => {
    const state = readFiltersFromSearch(
      "?start_date=2026-09-01&end_date=2026-09-30&branch=02",
      NOW,
    );
    expect(state.dateStart).toBe("2026-09-01");
    expect(state.dateEnd).toBe("2026-09-30");
    expect(state.competence).toBe("2026-09");
    expect(state.branch).toBe("02");
  });

  it("competência oficial vence e reconstrói datas", () => {
    const state = readFiltersFromSearch("?competence=2026-08", NOW);
    expect(state.dateStart).toBe("2026-08-01");
    expect(state.dateEnd).toBe("2026-08-31");
    expect(state.competence).toBe("2026-08");
  });

  it("ignora unidade desconhecida", () => {
    const state = readFiltersFromSearch("?branch=99", NOW);
    expect(state.branch).toBe("");
  });
});
