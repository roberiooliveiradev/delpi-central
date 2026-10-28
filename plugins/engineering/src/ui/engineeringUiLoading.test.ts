import { describe, expect, it } from "vitest";

import { HOME_COPY } from "../content/engineeringRouteCatalog";
import { EngineeringLoadingActivityCard } from "./engineeringUi";

describe("EngineeringLoadingActivityCard", () => {
  it("usa a factory canônica do plugin-ui (LoadingActivityCard)", () => {
    expect(typeof EngineeringLoadingActivityCard).toBe("function");
    expect(EngineeringLoadingActivityCard.name).toBe(
      "DashboardLoadingActivityCard",
    );
  });

  it("copy da Visão geral segue o padrão contextual dos portais", () => {
    expect(HOME_COPY.overview.loadingTitle).toBe(
      "Carregando indicadores de Engenharia",
    );
    expect(HOME_COPY.overview.loadingDescription).toContain(
      "fontes oficiais de LMPs e TRANSFORMA+",
    );
  });

  it("copy da Home segue o padrão contextual dos portais", () => {
    expect(HOME_COPY.loading.title).toBe("Preparando sua área de trabalho");
    expect(HOME_COPY.loading.description).toContain("LMPs autorizadas");
  });
});
