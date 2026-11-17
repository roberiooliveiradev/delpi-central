/** Verificações estruturais da ferramenta Processos > Balanceamento de
 * Linha — composição da página, contratos oficiais e isolamento do
 * rascunho. Comportamento dinâmico é coberto pelos unitários de
 * `yamazumi`/`methodCatalog` e pela E2E. */

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const page = readFileSync(join(here, "LineBalancingPage.tsx"), "utf8");
const feature = readFileSync(join(here, "../ProcessesFeature.tsx"), "utf8");
const hub = readFileSync(join(here, "../ProcessesPage.tsx"), "utf8");
const routes = readFileSync(
  join(here, "../../../app/engineeringRoutes.ts"),
  "utf8",
);
const catalog = readFileSync(
  join(here, "../../../content/engineeringRouteCatalog.ts"),
  "utf8",
);
const home = readFileSync(
  join(here, "../../home/HomePage.tsx"),
  "utf8",
);
const app = readFileSync(join(here, "../../../App.tsx"), "utf8");
const css = readFileSync(join(here, "../../../index.css"), "utf8");

describe("Processes card (PROC-01)", () => {
  it("catálogo tem a seção processes com os destinos da ferramenta", () => {
    expect(catalog).toContain('id: "processes"');
    expect(catalog).toContain("title: \"Processos\"");
    expect(catalog).toContain('id: "line-balancing"');
    expect(catalog).toContain("/apps/engineering/processes/line-balancing");
    expect(catalog).toContain('requiredPermission: "engineering.access"');
  });

  it("home mapeia ícones da seção e das rotas novas", () => {
    expect(home).toContain("processes:");
    expect(home).toContain('"line-balancing":');
  });
});

describe("Processes routing (PROC-02/03)", () => {
  it("EngineeringView inclui processes e o resolver aceita sub-paths", () => {
    expect(routes).toContain('"processes"');
    expect(routes).toContain('relativePath.startsWith("processes/")');
  });

  it("App monta ProcessesFeature sem passar por ProductsFeature", () => {
    expect(app).toContain('resolved.view === "processes"');
    expect(app).toContain("ProcessesFeature");
    expect(feature).not.toMatch(/from "\.\.\/products|import.*ProductsFeature/);
  });

  it("hub lista a ferramenta Balanceamento de Linha navegável", () => {
    expect(hub).toContain("Balanceamento de Linha");
    expect(hub).toContain("/apps/engineering/processes/line-balancing");
    expect(hub).toContain("navigateGovernedHref");
  });

  it("ferramentas futuras aparecem como planejamento, sem ação falsa", () => {
    expect(hub).toContain("Em planejamento");
    expect(hub).toContain("disabled: true");
  });
});

describe("BFF contracts (PROC-04/06/07)", () => {
  it("usa somente contratos do Engineering BFF — nunca API-DELPI direta", () => {
    expect(page).toContain("fetchProductRouting");
    expect(page).toContain("postProductLineBalance");
    expect(page).not.toContain("/apps/api-delpi");
    expect(page).not.toContain("api-delpi/v1");
  });

  it("estados honestos: sem produto, consultando, 403, 404, vazio, estágio", () => {
    expect(page).toContain("Informe o código do produto");
    expect(page).toContain("Consultando o roteiro oficial");
    expect(page).toContain("isForbidden");
    expect(page).toContain("isNotFound");
    expect(page).toContain("Roteiro oficial vazio");
    expect(page).toContain("Selecione a filial e o estágio produtivo");
  });

  it("estágio nunca é selecionado automaticamente", () => {
    expect(page).not.toContain("grouped.stages[0]");
    expect(page).toContain("?? null;");
  });
});

describe("M1 reuse + catálogo (PROC-07/08)", () => {
  it("reutiliza o domínio via postProductLineBalance, sem recalcular", () => {
    expect(page).toContain("postProductLineBalance(");
    expect(page).toContain("attachResult");
    expect(page).not.toContain("build_balance_result");
  });

  it("seletor de método lista os seis métodos do catálogo", () => {
    expect(page).toContain("BALANCING_METHODS.map");
    expect(page).toContain("setMethodId");
  });
});

describe("Yamazumi (PROC-09..12)", () => {
  it("configura postos via PostConfigurator e atribui só operações oficiais", () => {
    expect(page).toContain("PostConfigurator");
    expect(page).toContain("assignOperationToPost");
    expect(page).toContain("unassignedOperations");
  });

  it("gráfico empilhado com linha de takt e chrome corporativo", () => {
    expect(page).toContain("RoutingSeriesChart");
    expect(page).toContain('"stacked_bar", "bar"');
    expect(page).toContain("buildYamazumiChartSpec");
    expect(page).toContain("Takt");
  });

  it("tempos desconhecidos e não atribuídas são explícitos", () => {
    expect(page).toContain("UNKNOWN");
    expect(page).toContain("não atribuída");
    expect(page).toContain("AGGREGATE_TIME_CATEGORY");
  });
});

describe("Persistência e cenários (PROC-13/14/15)", () => {
  it("rascunho usa prefixo próprio do namespace Processos", () => {
    expect(page).toContain("engineering:processes:line-balance");
    expect(page).toContain("storagePrefix");
    expect(page).not.toContain("STUDY_STORAGE_PREFIX");
  });

  it("limpar estudo exige confirmação e só limpa o rascunho local", () => {
    expect(page).toContain("EngineeringConfirmDialog");
    expect(page).toContain("Limpar estudo");
    expect(page).toContain("confirmClear");
    expect(page).toContain("rascunho da Ficha do Produto é alterado");
  });

  it("cenários compartilham chips e o limite máximo do contrato", () => {
    expect(page).toContain("EngineeringScopeChipBar");
    expect(page).toContain("study.addScenario");
    expect(page).toContain("study.maxScenarios");
  });
});

describe("Exports e segurança (PROC-16/19)", () => {
  it("exportação inclui contexto, método, proveniência e limitação", () => {
    expect(page).toContain("SIMULATION");
    expect(page).toContain("proveniencia");
    expect(page).toContain("limitacao");
    expect(page).toContain("buildYamazumiExportPayload");
  });

  it("não grava roteiro nem chama write endpoints", () => {
    expect(page).not.toContain("putProduct");
    expect(page).not.toContain("patchProduct");
    expect(page).not.toContain("deleteProduct");
  });
});

describe("Layout (PROC-17/18)", () => {
  it("classes de composição próprias existem no CSS do MFE", () => {
    for (const cls of [
      "engineering-processes__lookup",
      "engineering-processes__yamazumi-grid",
      "engineering-processes__yamazumi-legend",
      "engineering-processes__unassigned",
      "engineering-processes__method-list",
    ]) {
      expect(css).toContain(`.${cls}`);
    }
  });
});
