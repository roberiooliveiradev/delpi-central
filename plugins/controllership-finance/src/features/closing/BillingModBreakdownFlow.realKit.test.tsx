/**
 * R09 — prova INTEGRADA do fluxo real (doc 154 §11, CF-PROC0072-R09):
 *
 *   payload fiel da api-delpi
 *     → projeção BFF vigente (espelhada de
 *       build_billing_mod_breakdown_projection)
 *     → getBillingModBreakdown() + normalizePayload()
 *     → BillingModBreakdownPage → AnchorDetail
 *     → DataTableSection REAL do @delpi/plugin-ui
 *
 * A prova NÃO para no cliente: renderiza a página e verifica o
 * detalhe MOD exibido (produto componente, unidade MOD, operação,
 * recurso, item, sourceOp, ausências tipadas honestas).
 */
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// `?raw` de assets fora do root não resolve no Vitest (mesma
// limitação documentada do BillingModBreakdownTable.realKit.test).
vi.mock("../../../../plugin-ui/src/brand/delpiLogoMark", () => ({
  DELPI_LOGO_MARK_SVG: "",
  DelpiLogoMark: () => null,
}));

const httpGetMock = vi.fn();
vi.mock("../../api/httpClient", () => ({
  cfApiUrl: (path: string) => path,
  httpGet: (...args: unknown[]) => httpGetMock(...args),
}));

import { BillingModBreakdownPage } from "./BillingModBreakdownPage";
import REAL_BFF_2026_09 from "../../test/fixtures/billingModBreakdown.realBff.2026-09.json";

const CONTEXT = { period: "2026-09" };

/** Saída real de GetBillingModBreakdownUseCase: emite `explodedProduct`,
 *  `unit`, `anchorProduct`, `modItemState`, `diagnostics`; NUNCA emite
 *  `product`, `modUnit`, `productDescription` ou `costProduct`. */
const PRODUCER_ANCHOR = {
  product: "80014579",
  branch: "01",
  billedQty: 0.01,
  modLines: [
    {
      level: "02",
      anchorProduct: "80014579",
      explodedProduct: "80014579",
      modItem: "MOD349",
      modDescription: "Mão de obra inspeção",
      unit: "HH",
      operation: "030",
      operationDescription: "INSPECIONAR",
      resource: "CT-70",
      stdTime: { value: 0.01, state: "shy_frozen_op" },
      sourceOp: "000123",
      propagatedQty: 0.01,
      hours: { value: 0.0001, state: "computed" },
      costUnit: {
        value: null,
        state: "source_missing",
        reason: "cost_rate_basis_unavailable",
      },
      costTotal: { value: null, state: "source_missing" },
      modItemState: "mapped",
    },
    {
      level: "04",
      anchorProduct: "80014579",
      explodedProduct: "COMP-77",
      modItem: "MOD112",
      modDescription: "Mão de obra solda",
      unit: "HH",
      operation: "040",
      resource: "CT-19",
      stdTime: { value: 0.005, state: "sg2_cadastral" },
      propagatedQty: 0.02,
      hours: { value: null, state: "source_missing" },
      costUnit: { value: null, state: "source_missing" },
      costTotal: { value: null, state: "source_missing" },
      modItemState: "mapped",
    },
  ],
  sourceMissing: ["cost_rate_basis"],
  diagnostics: {
    productsWithoutRouteOperations: [],
    unmappedResourceMod: [],
  },
};

/** Espelho fiel de build_billing_mod_breakdown_projection (BFF):
 *  pass-through dos dados do produtor + officiality, officialParity,
 *  parityEvidence estática e limitations governadas. Campos do
 *  produtor passam inalterados — a BFF não renomeia nada hoje. */
function bffProjectedPayload() {
  return {
    report: "billing-mod-breakdown",
    reportId: "R09",
    period: "2026-09",
    branch: "all",
    anchors: [PRODUCER_ANCHOR],
    limitations: [
      "A seleção do roteiro congelado (última OP com SHY) pode divergir do snapshot histórico usado pelo DLP204.",
      "A taxa histórica de MOD não foi localizada: costUnit/costTotal/costProduct são ausência tipada, nunca zero.",
      "Paridade oficial pendente de homologação item a item pela Controladoria (DR-3).",
    ],
    officiality: "operational_view",
    officialParity: "pending",
    parityEvidence: {
      scope: {
        referencePeriod: "2026-09",
        branches: ["01", "02"],
        artifact: "Fat x MOD.xlsb (DLP204)",
        measuredAt: "2026-11-01",
        gate: "G042 (doc 144)",
        homologationStatus: "pending (DR-3, Controladoria)",
      },
      metrics: {
        artifactLines: 4476,
        calculatedLines: 4659,
        matchedKeys: 3694,
        keyCoveragePct: 82.5,
        qtdFatCorrectPct: 99.6,
        stdTimeCorrectPct: 82.2,
        hoursCorrectPct: 81.9,
        missingLines: 782,
        extraLines: 965,
      },
      semantics:
        "Historical point-in-time comparison between the reconstructed " +
        "engine and the DLP204 artifact for 2026-09.",
    },
    provenance: { engine: "api-delpi" },
  };
}

function mockBffResponse() {
  httpGetMock.mockResolvedValue({
    success: true,
    message: "Faturamento × MOD carregado (visão operacional).",
    data: bffProjectedPayload(),
  });
}

async function renderLoadedPage(anchorProduct = "80014579") {
  const utils = render(
    <BillingModBreakdownPage reportContext={CONTEXT} />,
  );
  await screen.findByText("Faturamento × MOD — R09");
  await within(utils.container.querySelector("tbody")!).findAllByText(
    anchorProduct,
  );
  return utils;
}

async function openDetail(container: HTMLElement, anchorProduct = "80014579") {
  fireEvent.click(
    await screen.findByRole("button", {
      name: new RegExp(
        `Ver operações MOD do produto ${anchorProduct}, filial 01`,
      ),
    }),
  );
  await screen.findByText(
    new RegExp(`Operações MOD — ${anchorProduct}`),
  );
  const region = container.querySelector("#cf-r09-anchor-detail");
  expect(region).not.toBeNull();
  return within(region as HTMLElement);
}

beforeEach(() => {
  httpGetMock.mockReset();
});

afterEach(cleanup);

describe("R09 — fluxo integrado produtor → BFF → normalize → página → detalhe", () => {
  it("produto componente e unidade MOD chegam ao detalhe renderizado", async () => {
    mockBffResponse();
    const { container } = await renderLoadedPage();
    const detail = await openDetail(container);

    // header do detalhe identifica âncora e filial (título do card)
    screen.getByRole("heading", {
      name: /Operações MOD — 80014579 \/ Filial 01/,
    });
    // produto componente do nível 04 é distinto da âncora (COMP-77)
    expect(detail.getAllByText("COMP-77").length).toBeGreaterThan(0);
    // unidade MOD normalizada (unit → modUnit) aparece nas duas linhas
    expect(detail.getAllByText("HH")).toHaveLength(2);
    // operação, descrição, recurso e item MOD intactos
    detail.getByText("030");
    detail.getByText("INSPECIONAR");
    detail.getByText("CT-70");
    detail.getByText("MOD349");
    detail.getByText("Mão de obra inspeção");
    // sourceOp preservado
    detail.getByText("000123");
    // nenhuma linha foi omitida pela normalização (2 linhas de dados)
    const rows = (container.querySelector(
      "#cf-r09-anchor-detail",
    ) as HTMLElement).querySelectorAll("tbody tr");
    expect(rows).toHaveLength(2);
  });

  it("tempos/horas sem transformação financeira; ausências nunca viram zero", async () => {
    mockBffResponse();
    const { container } = await renderLoadedPage();
    const detail = await openDetail(container);

    // stdTime 0.01 exibido; hours 0.0001 não arredonda para «0»
    expect(detail.getAllByText("0,01").length).toBeGreaterThan(0);
    expect(detail.getAllByText(/0,0001/).length).toBeGreaterThan(0);
    // custos ausentes = ausência tipada, nunca «0» nem valor inventado
    expect(detail.getAllByText("fonte ausente").length).toBeGreaterThan(0);
    // costProduct não é emitido pelo produtor → «—» honesto
    const detailRows = Array.from(
      (container.querySelector("#cf-r09-anchor-detail") as HTMLElement)
        .querySelectorAll("tbody tr"),
    );
    for (const tr of detailRows) {
      const cells = tr.querySelectorAll("td");
      expect(cells[cells.length - 2].textContent).toBe("—");
    }
    // descrição de produto ausente não é simulada em lugar nenhum
    expect(detail.queryByText(/Trafo|Transformador/)).toBeNull();
  });

  it("master recebe payload projetado: âncoras, busca por código e evidência histórica", async () => {
    mockBffResponse();
    const { container } = await renderLoadedPage();

    // KPI âncoras derivado do payload
    screen.getByText("Âncoras produto/filial");
    // busca por código no kit real encontra a âncora
    const input = container.querySelector(
      "input[type=\"search\"]",
    ) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "80014579" } });
    const masterTbody = within(
      container.querySelectorAll("tbody")[0] as HTMLElement,
    );
    await masterTbody.findAllByText("80014579");
    // evidência histórica projetada pela BFF aparece datada
    screen.getByText(/Evidência histórica de paridade — referência 2026-09/);
    screen.getByText(/Pendente \(DR-3, Controladoria\)/);
    // limitações governadas da BFF alcançam o disclosure
    screen.getByText(/Limitações e divergências conhecidas/);
  });

  it("resposta REAL sanitizada da BFF (2026-09, âncora 90260139): todos os campos renderizam", async () => {
    httpGetMock.mockResolvedValue(REAL_BFF_2026_09);
    const { container } = await renderLoadedPage("90260139");
    const detail = await openDetail(container, "90260139");

    // 6 linhas reais preservadas pela cadeia completa
    const detailRows = (container.querySelector(
      "#cf-r09-anchor-detail",
    ) as HTMLElement).querySelectorAll("tbody tr");
    expect(detailRows).toHaveLength(6);
    // componente real do nível 04 (50212205) distinto da âncora (90260139)
    expect(detail.getAllByText("50212205").length).toBeGreaterThan(0);
    // unidades MOD reais: HR (5×) e H (1×)
    expect(detail.getAllByText("HR")).toHaveLength(5);
    expect(detail.getAllByText("H")).toHaveLength(1);
    // itens MOD e descrições reais (MOD21101 ocorre em 3 operações)
    detail.getByText("MOD254");
    expect(detail.getAllByText("MOD21101")).toHaveLength(3);
    expect(
      detail.getAllByText(/MAO DE OBRA DIRETA DE MONTAGEM/),
    ).toHaveLength(3);
    // OPs de referência reais distintas por nível
    expect(detail.getAllByText("24801801001")).toHaveLength(5);
    detail.getByText("24801801002");
    // tempo padrão real e horas computadas preservadas
    detail.getByText("1,07");
    detail.getByText(/0,0504|0,05/);
    // custos reais: ausência tipada com motivo acessível, nunca zero
    expect(detail.getAllByText("fonte ausente").length).toBeGreaterThan(0);
    expect(
      detail.getAllByTitle(/Taxa de MOD sem fonte comprovada/).length,
    ).toBeGreaterThan(0);
  });

  it("envelope de erro tipado da BFF renderiza estado honesto, sem técnica exposta", async () => {
    httpGetMock.mockRejectedValue({
      status: 502,
      message: "api-delpi gateway timeout",
    });
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    expect(
      await screen.findByText(
        /Não foi possível carregar o relatório R09/,
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/api-delpi gateway timeout/)).toBeNull();
  });
});
