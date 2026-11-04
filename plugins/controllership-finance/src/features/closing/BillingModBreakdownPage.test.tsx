/**
 * R09 — redesign master/detail (doc 153): tabela de âncoras,
 * detalhe inline, estados tipados e histórico datado.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { BillingModBreakdownPage } from "./BillingModBreakdownPage";
import {
  type BillingModBreakdownPayload,
} from "../../api/billingModBreakdownApi";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getMod = vi.fn();
vi.mock("../../api/billingModBreakdownApi", () => ({
  getBillingModBreakdown: (...args: unknown[]) => getMod(...args),
}));

const CONTEXT = { period: "2026-10" };

function anchor(overrides: Record<string, unknown> = {}) {
  return {
    branch: "01",
    product: "80014579",
    productDescription: "Trafo teste",
    billedQty: 0.01,
    modLines: [],
    ...overrides,
  };
}

function payload(overrides: Record<string, unknown> = {}) {
  return {
    report: "billing-mod-breakdown",
    period: "2026-10",
    branch: "all",
    anchors: [],
    limitations: [],
    ...overrides,
  } as BillingModBreakdownPayload;
}

beforeEach(() => {
  getMod.mockReset();
});

describe("R09 — Faturamento × MOD (master/detail)", () => {
  it("renderiza hero com indicadores reais e tabela de âncoras, sem cards por produto", async () => {
    getMod.mockResolvedValue(
      payload({
        anchors: [
          anchor({ product: "A1", modLines: [{ level: "02" }] }),
          anchor({ product: "B2", branch: "02", billedQty: 0 }),
          anchor({ product: "C3" }),
        ],
      }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);

    expect(
      await screen.findByText("Faturamento × MOD — R09"),
    ).toBeTruthy();
    // KPIs derivados do payload
    expect(screen.getByText("Âncoras produto/filial")).toBeTruthy();
    expect(screen.getByText("3")).toBeTruthy();
    expect(screen.getByText("Âncoras sem linhas")).toBeTruthy();
    // tabela master com linhas por âncora
    expect(screen.getByText("A1")).toBeTruthy();
    expect(screen.getByText("B2")).toBeTruthy();
    // zero real preservado na quantidade faturada
    expect(screen.getAllByText("0").length).toBeGreaterThan(0);
  });

  it("mesmo produto em filiais distintas gera linhas e chaves separadas", async () => {
    getMod.mockResolvedValue(
      payload({
        anchors: [
          anchor({ product: "P1", branch: "01" }),
          anchor({ product: "P1", branch: "02" }),
        ],
      }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    await screen.findAllByText("P1");
    const buttons = screen.getAllByRole("button", {
      name: /Ver operações MOD do produto P1, filial/,
    });
    expect(buttons.length).toBe(2);
  });

  it("selecionar âncora exibe detalhe com operações e estados tipados", async () => {
    getMod.mockResolvedValue(
      payload({
        anchors: [
          anchor({
            product: "P9",
            modLines: [
              {
                level: "02",
                operation: "INSPECIONAR",
                resource: "CT-70",
                modItem: "MOD349",
                propagatedQty: 0.01,
                stdTime: { value: 0.01, state: "AVAILABLE" },
                hours: { value: null, state: "SOURCE_MISSING" },
                costUnit: { value: null, state: "NOT_APPLICABLE" },
                costTotal: { value: null, state: "UNKNOWN_X" },
                sourceOp: "000123",
              },
            ],
          }),
        ],
      }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);

    const open = await screen.findByRole("button", {
      name: /Ver operações MOD do produto P9/,
    });
    fireEvent.click(open);

    await screen.findByText(/Operações MOD — P9/);
    expect(screen.getByText("INSPECIONAR")).toBeTruthy();
    // tempo padrão real exibido; null NUNCA vira 0
    expect(screen.getAllByText("0,01").length).toBeGreaterThan(0);
    expect(screen.getByText("fonte ausente")).toBeTruthy();
    expect(screen.getByText("não aplicável")).toBeTruthy();
    expect(screen.getByText("não informado pela fonte")).toBeTruthy();
    expect(screen.queryByText(/indisponível$/)).toBeNull();
  });

  it("âncora sem linhas mostra mensagem factual, sem causa inventada", async () => {
    getMod.mockResolvedValue(
      payload({ anchors: [anchor({ product: "P0" })] }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Ver operações MOD do produto P0/,
      }),
    );
    expect(
      await screen.findByText(/Nenhuma linha MOD retornada para esta âncora/),
    ).toBeTruthy();
    expect(screen.queryByText(/sem roteiro/)).toBeNull();
  });

  it("evidência histórica aparece datada e nunca como KPI corrente", async () => {
    getMod.mockResolvedValue(
      payload({
        anchors: [anchor()],
        parityEvidence: {
          scope: {
            referencePeriod: "09/2026",
            branches: ["01", "02"],
            artifact: "DLP204",
            measuredAt: "2026-10-30",
            gate: "G042",
            homologationStatus: "PENDING",
          },
          metrics: {
            artifactLines: 4476,
            calculatedLines: 4476,
            matchedKeys: 3694,
            keyCoveragePct: 82.5,
            qtdFatCorrectPct: 0,
            stdTimeCorrectPct: 0,
            hoursCorrectPct: 0,
            missingLines: 0,
            extraLines: 0,
          },
          semantics: "Cobertura de chaves do estudo.",
        },
      }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    await screen.findAllByText("Produtos faturados");
    expect(
      screen.getByText(/Evidência histórica de paridade — referência 09\/2026/),
    ).toBeTruthy();
    expect(screen.getByText(/não comprova a competência corrente/)).toBeTruthy();
    // o histórico fica em disclosure — não é KPI
    expect(screen.queryByText(/82,5% paridade/)).toBeNull();
  });

  it("erro de consulta exibe ação de tentar novamente", async () => {
    getMod
      .mockRejectedValueOnce({ status: 500, message: "falha" })
      .mockResolvedValueOnce(payload({ anchors: [anchor()] }));
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);

    const retry = await screen.findByRole("button", {
      name: "Tentar novamente",
    });
    fireEvent.click(retry);
    expect((await screen.findAllByText("Produtos faturados")).length).toBeGreaterThan(0);
  });

  it("vazio real renderiza empty state, sem cards falsos", async () => {
    getMod.mockResolvedValue(payload({ anchors: [] }));
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    expect(
      await screen.findByText(
        /Nenhuma âncora faturada encontrada/,
      ),
    ).toBeTruthy();
  });

  it("coluna Custo produto preserva valor real e ausência tipada", async () => {
    getMod.mockResolvedValue(
      payload({
        anchors: [
          anchor({
            product: "CP1",
            modLines: [
              {
                level: "02",
                operation: "MONTAR",
                costProduct: { value: 1234.5, state: "computed" },
              },
              {
                level: "04",
                operation: "SOLDAR",
                costProduct: { value: null, state: "source_missing" },
              },
            ],
          }),
        ],
      }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Ver operações MOD do produto CP1/,
      }),
    );
    await screen.findAllByText("Custo produto");
    expect(screen.getByText("1.234,5")).toBeTruthy();
    expect(screen.getAllByText("fonte ausente").length).toBeGreaterThan(0);
  });

  it("data civil do histórico não perde um dia por fuso (2026-11-01 → 01/11/2026)", async () => {
    getMod.mockResolvedValue(
      payload({
        anchors: [anchor()],
        parityEvidence: {
          scope: {
            referencePeriod: "09/2026",
            branches: ["01"],
            artifact: "DLP204",
            measuredAt: "2026-11-01",
            gate: "G042",
            homologationStatus: "pending (DR-3, Controladoria)",
          },
          metrics: {
            artifactLines: 1,
            calculatedLines: 1,
            matchedKeys: 1,
            keyCoveragePct: 0,
            qtdFatCorrectPct: 0,
            stdTimeCorrectPct: 0,
            hoursCorrectPct: 0,
            missingLines: 0,
            extraLines: 0,
          },
          semantics: "x",
        },
      }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    await screen.findAllByText("Produtos faturados");
    expect(screen.getByText(/Medido em:\s*01\/11\/2026/)).toBeTruthy();
    // status de homologação traduzido, sufixo preservado
    expect(
      screen.getByText(/Pendente \(DR-3, Controladoria\)/),
    ).toBeTruthy();
  });

  it("estados reais lowercase do produtor: source_missing e precisão pequena", async () => {
    getMod.mockResolvedValue(
      payload({
        anchors: [
          anchor({
            product: "SM1",
            modLines: [
              {
                level: "02",
                stdTime: { value: 0.00001, state: "shy_frozen_op" },
                costUnit: { value: null, state: "source_missing" },
              },
            ],
          }),
        ],
      }),
    );
    render(<BillingModBreakdownPage reportContext={CONTEXT} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Ver operações MOD do produto SM1/,
      }),
    );
    await screen.findByText(/Operações MOD — SM1/);
    // 0,00001 nunca renderiza como "0"
    expect(screen.getByText(/0,00001/)).toBeTruthy();
    expect(screen.getAllByText("fonte ausente").length).toBeGreaterThan(0);
  });

  it("troca de filial limpa seleção e dispara nova consulta", async () => {
    getMod.mockResolvedValue(
      payload({ anchors: [anchor({ product: "B1", branch: "01" })] }),
    );
    const { container } = render(
      <BillingModBreakdownPage reportContext={CONTEXT} />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Ver operações MOD do produto B1/,
      }),
    );
    await screen.findByText(/Operações MOD — B1/);
    fireEvent.change(container.querySelector(".cf-hero-filters select")!, {
      target: { value: "02" },
    });
    await screen.findAllByText("Produtos faturados");
    expect(
      screen.queryByText(/Operações MOD — B1/),
    ).toBeNull();
    expect(getMod).toHaveBeenLastCalledWith("2026-10", "02");
  });

  it("detalhe some se âncora selecionada não existe no novo payload", async () => {
    getMod
      .mockResolvedValueOnce(
        payload({ anchors: [anchor({ product: "OLD1" })] }),
      )
      .mockResolvedValueOnce(
        payload({ anchors: [anchor({ product: "NEW1", branch: "02" })] }),
      );
    const { container } = render(
      <BillingModBreakdownPage reportContext={CONTEXT} />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Ver operações MOD do produto OLD1/,
      }),
    );
    await screen.findByText(/Operações MOD — OLD1/);
    fireEvent.change(container.querySelector(".cf-hero-filters select")!, {
      target: { value: "02" },
    });
    await screen.findByText("NEW1");
    expect(
      screen.queryByText(/Operações MOD — OLD1/),
    ).toBeNull();
  });
});
