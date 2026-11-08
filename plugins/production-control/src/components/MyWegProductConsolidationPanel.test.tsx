// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HttpRequestError } from "../api/httpClient";
import type { MyWegCompareProductsPayload } from "../types";
import { MyWegProductConsolidationPanel } from "./MyWegProductConsolidationPanel";

const fetchProducts = vi.fn();
const fetchObservation = vi.fn();
const fetchObservationItems = vi.fn();

vi.mock("@delpi/plugin-ui/index", () => ({
  HelpTooltip: () => null,
}));

vi.mock("../api/ppcApi", () => ({
  fetchMyWegNeedBatchesCompareProducts: (...args: unknown[]) => fetchProducts(...args),
  fetchMyWegInvoiceObservation: (...args: unknown[]) => fetchObservation(...args),
  fetchMyWegInvoiceObservationItems: (...args: unknown[]) =>
    fetchObservationItems(...args),
}));

vi.mock("./PpcConfirmModal", () => ({
  HostContainedWideDialog: ({
    open,
    title,
    children,
    onClose,
  }: {
    open: boolean;
    title: string;
    children: ReactNode;
    onClose: () => void;
  }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        <button type="button" onClick={onClose}>
          Fechar
        </button>
        {children}
      </div>
    ) : null,
}));

vi.mock("./dataTableUi", () => ({
  DataTableSection: ({
    rows,
    columns,
    onRowClick,
  }: {
    rows: Array<{ productKey: string }>;
    columns: Array<{
      key: string;
      render: (row: { productKey: string }) => unknown;
    }>;
    onRowClick?: (row: { productKey: string }) => void;
  }) => (
    <div data-testid="products-table">
      {rows.map((row) => (
        <div key={row.productKey} data-testid={`row-${row.productKey}`}>
          <button type="button" onClick={() => onRowClick?.(row)}>
            row-{row.productKey}
          </button>
          {columns.map((column) => (
            <div key={`${row.productKey}-${column.key}`} data-testid={`col-${column.key}`}>
              {column.render(row) as ReactNode}
            </div>
          ))}
        </div>
      ))}
    </div>
  ),
}));

const basePayload: MyWegCompareProductsPayload = {
  branch: "02",
  scope: {
    customerName: "WEG",
    protheusCustomerCode: "000001",
    protheusCustomerStore: "09",
  },
  fromBatch: {
    id: "from",
    collectionId: "c1",
    branch: "02",
    status: "accepted",
    collectedAt: "2026-11-06T08:00:00-03:00",
    collectionDate: "2026-11-06",
    importedAt: "2026-11-06T08:00:00-03:00",
    recordCount: 2,
    totals: { quantidade_original_un: "2", quantidade_mi: "0" },
  },
  toBatch: {
    id: "to",
    collectionId: "c2",
    branch: "02",
    status: "accepted",
    collectedAt: "2026-11-07T08:00:00-03:00",
    collectionDate: "2026-11-07",
    importedAt: "2026-11-07T08:00:00-03:00",
    recordCount: 2,
    totals: { quantidade_original_un: "2", quantidade_mi: "0" },
  },
  page: 1,
  pageSize: 50,
  total: 1,
  totalProductsCompared: 1,
  totalProductsChanged: 1,
  changesOnly: true,
  search: "",
  invoiceMode: "portal",
  totals: {
    previousQuantityUn: "2",
    currentQuantityUn: "2",
    deltaQuantityUn: "0",
    postedQuantityUn: "0",
    observedDeltaUn: "0",
    adjustedPlanningDeltaUn: "0",
    compatibleReductionUn: "0",
  },
  portalInvoices: {
    status: "complete",
    coverage: "complete",
    period: {
      fromDocumentDate: "2026-11-06",
      toDocumentDateExclusive: "2026-11-07",
      start: "2026-11-06",
      end: "2026-11-06",
      days: ["2026-11-06"],
    },
    coveredDates: ["2026-11-06"],
    missingDates: [],
    coveredDayCount: 1,
    missingDayCount: 0,
    canonicalObservations: [
      {
        documentDate: "2026-11-06",
        status: "selected",
        observationId: "obs-1",
      },
    ],
    disclaimer: "Conciliação analítica",
  },
  items: [
    {
      productKey: "code:80016354",
      identityKind: "verified_code",
      identityConfirmed: true,
      identityReliable: true,
      verifiedProductCode: "80016354",
      materialWegTratado: "MAT-001",
      previousQuantityUn: "2",
      currentQuantityUn: "2",
      deltaQuantityUn: "0",
      percentChange: "0",
      previousRemessaCount: 1,
      currentRemessaCount: 1,
      hasRemessaChanges: true,
      situation: "stable_with_date_changes",
      observedDeltaUn: "0",
      postedQuantityUn: "0",
      adjustedPlanningDeltaUn: "0",
      compatibleReductionUn: "0",
      invoiceMatchStatus: "none",
      managerialStatus: "other_movement",
      residualUnexplainedUn: null,
      remessas: [
        {
          remessa: "2026-11-12",
          previousQuantityUn: "2",
          currentQuantityUn: "0",
          deltaQuantityUn: "-2",
          movement: "disappeared",
        },
        {
          remessa: "2026-11-10",
          previousQuantityUn: "0",
          currentQuantityUn: "2",
          deltaQuantityUn: "2",
          movement: "appeared",
        },
      ],
      probableDateShifts: [],
    },
  ],
  disclaimer: "Totais consolidados",
};

function portalPayload(
  overrides: Partial<MyWegCompareProductsPayload> = {},
): MyWegCompareProductsPayload {
  return {
    ...basePayload,
    invoiceMode: "portal",
    totals: {
      ...basePayload.totals,
      postedQuantityUn: "10",
      observedDeltaUn: "0",
      adjustedPlanningDeltaUn: "10",
      compatibleReductionUn: "0",
    },
    portalInvoices: {
      status: "complete",
      coverage: "complete",
      period: {
        fromDocumentDate: "2026-11-06",
        toDocumentDateExclusive: "2026-11-07",
        start: "2026-11-06",
        end: "2026-11-06",
        days: ["2026-11-06"],
      },
      coveredDates: ["2026-11-06"],
      missingDates: [],
      coveredDayCount: 1,
      missingDayCount: 0,
      canonicalObservations: [
        {
          documentDate: "2026-11-06",
          status: "selected",
          observationId: "obs-1",
        },
      ],
      disclaimer: "Conciliação analítica",
    },
    items: [
      {
        ...basePayload.items[0],
        observedDeltaUn: "0",
        postedQuantityUn: "10",
        adjustedPlanningDeltaUn: "10",
        compatibleReductionUn: "0",
        invoiceMatchStatus: "reconciled",
        managerialStatus: "other_movement",
        residualUnexplainedUn: null,
        portalInvoiceMaterials: [
          {
            materialWeg: "MAT-001",
            postedQuantityUn: "10",
            attributedToProductKey: "code:80016354",
          },
        ],
        portalInvoiceSources: ["obs-1"],
      },
    ],
    ...overrides,
  };
}

/** Caso real: 90263746 / redução 2450 / NF 000017061. */
function invoiced90263746Payload(): MyWegCompareProductsPayload {
  return portalPayload({
    totals: {
      previousQuantityUn: "8348",
      currentQuantityUn: "5898",
      deltaQuantityUn: "-2450",
      observedDeltaUn: "-2450",
      postedQuantityUn: "2450",
      compatibleReductionUn: "2450",
      adjustedPlanningDeltaUn: "0",
    },
    items: [
      {
        productKey: "code:90263746",
        identityKind: "verified_code",
        identityConfirmed: true,
        identityReliable: true,
        verifiedProductCode: "90263746",
        materialWegTratado: "17382643",
        previousQuantityUn: "8348",
        currentQuantityUn: "5898",
        deltaQuantityUn: "-2450",
        percentChange: "-29.35",
        previousRemessaCount: 3,
        currentRemessaCount: 2,
        hasRemessaChanges: true,
        situation: "decreased",
        observedDeltaUn: "-2450",
        postedQuantityUn: "2450",
        compatibleReductionUn: "2450",
        adjustedPlanningDeltaUn: "0",
        invoiceMatchStatus: "reconciled",
        managerialStatus: "invoiced",
        managerialReason: "full_compatible_reduction",
        managerialExplanation:
          "Redução de 2450 UN integralmente compatível com a NF MyWEG observada. Nenhuma redução residual identificada.",
        residualUnexplainedUn: "0",
        remessaInvoicingContext: "compatible_on_reduced_lines",
        portalInvoiceMaterials: [
          {
            materialWeg: "17382643",
            postedQuantityUn: "2450",
            attributedToProductKey: "code:90263746",
          },
        ],
        portalInvoiceSources: ["obs-1"],
        remessas: [
          {
            remessa: "2026-11-06",
            previousQuantityUn: "998",
            currentQuantityUn: "0",
            deltaQuantityUn: "-998",
            movement: "disappeared",
            managerialRemessaContext: "compatible_with_invoicing",
          },
          {
            remessa: "2026-11-11",
            previousQuantityUn: "1750",
            currentQuantityUn: "298",
            deltaQuantityUn: "-1452",
            movement: "decreased",
            managerialRemessaContext: "compatible_with_invoicing",
          },
          {
            remessa: "2026-11-20",
            previousQuantityUn: "5600",
            currentQuantityUn: "5600",
            deltaQuantityUn: "0",
            movement: "unchanged",
          },
        ],
        probableDateShifts: [],
      },
    ],
  });
}

describe("MyWegProductConsolidationPanel", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    fetchProducts.mockReset();
    fetchObservation.mockReset();
    fetchObservationItems.mockReset();
    fetchProducts.mockResolvedValue(basePayload);
    fetchObservation.mockResolvedValue({
      id: "obs-1",
      collectionId: "col-1",
      branch: "02",
      status: "accepted",
      observationStatus: "with_records",
      documentDate: "2026-11-06",
      recordCount: 1,
      totalQuantityUn: "2450",
    });
    fetchObservationItems.mockResolvedValue({
      branch: "02",
      observationId: "obs-1",
      collectionId: "col-1",
      documentDate: "2026-11-06",
      observationStatus: "with_records",
      page: 1,
      pageSize: 50,
      total: 2,
      items: [
        {
          id: "item-1",
          sourceLineNo: 1,
          invoiceNumber: "000017061",
          invoiceSeries: "2",
          materialWeg: "17382643",
          quantityOriginal: "2450",
          sourceUnit: "UN",
          quantityUn: "2450",
          unitComparability: "exact",
          departureDate: "2026-11-06",
        },
        {
          id: "item-2",
          sourceLineNo: 2,
          invoiceNumber: "000999",
          invoiceSeries: "1",
          materialWeg: "OUTRO",
          quantityOriginal: "5",
          sourceUnit: "UN",
          quantityUn: "5",
          unitComparability: "exact",
          departureDate: "2026-11-06",
        },
      ],
    });
  });

  it("consulta sempre com invoiceMode=portal sem toggle Necessidades/Conciliação", async () => {
    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="cabo" />,
    );

    await waitFor(() => {
      expect(fetchProducts).toHaveBeenCalled();
    });
    expect(fetchProducts.mock.calls[0][0]).toMatchObject({
      fromBatchId: "from",
      toBatchId: "to",
      search: "cabo",
      invoiceMode: "portal",
    });
    expect(
      screen.queryByRole("button", { name: /^Necessidades$/i }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: /^Conciliação MyWEG$/i }),
    ).toBeNull();
    expect(
      screen.getByRole("button", { name: /Atualizar conciliação/i }),
    ).toBeTruthy();
  });

  it("abre o detalhe em modal ao clicar em Detalhes", async () => {
    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("products-table")).toBeTruthy();
    });

    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /^detalhes$/i }));

    const dialog = screen.getByRole("dialog", { name: /Produto 80016354/i });
    expect(dialog).toBeTruthy();
    expect(screen.getByText(/Por data de remessa/i)).toBeTruthy();
    expect(screen.getByText("12/11/2026")).toBeTruthy();
    expect(screen.getByTestId("products-table")).toBeTruthy();
  });

  it("fecha o modal e mantém a lista visível", async () => {
    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("products-table")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: /^row-/i }));
    expect(screen.getByRole("dialog")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /^fechar$/i }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByTestId("products-table")).toBeTruthy();
  });

  it("exibe Faturado no caso 90263746 sem vermelho de cancelamento", async () => {
    fetchProducts.mockResolvedValue(invoiced90263746Payload());
    fetchObservationItems.mockResolvedValue({
      branch: "02",
      observationId: "obs-1",
      collectionId: "col-1",
      documentDate: "2026-11-06",
      observationStatus: "with_records",
      page: 1,
      pageSize: 50,
      total: 1,
      items: [
        {
          id: "item-1",
          sourceLineNo: 1,
          invoiceNumber: "000017061",
          invoiceSeries: "2",
          materialWeg: "17382643",
          quantityOriginal: "2450",
          sourceUnit: "UN",
          quantityUn: "2450",
          unitComparability: "exact",
          departureDate: "2026-11-06",
        },
      ],
    });

    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("col-managerial").textContent).toMatch(/Faturado/i);
    });
    expect(screen.getByTestId("col-posted").textContent).toContain("2.450");
    expect(screen.getByTestId("col-residual").textContent).toContain("0");
    expect(screen.getByTestId("col-observed").innerHTML).toContain("delta--invoiced");

    fireEvent.click(screen.getByRole("button", { name: /^detalhes$/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/integralmente compatível com a NF MyWEG/i),
      ).toBeTruthy();
    });
    expect(screen.getAllByText(/Compatível com faturamento/i).length).toBeGreaterThanOrEqual(
      2,
    );
    expect(screen.queryByText(/cancelamento/i)).toBeNull();

    await waitFor(() => {
      expect(screen.getByText("000017061")).toBeTruthy();
    });
    expect(screen.getByText("Notas fiscais relacionadas")).toBeTruthy();
  });

  it("destaca residual em faturamento parcial", async () => {
    fetchProducts.mockResolvedValue(
      portalPayload({
        items: [
          {
            ...basePayload.items[0],
            productKey: "code:partial",
            verifiedProductCode: "partial",
            previousQuantityUn: "2450",
            currentQuantityUn: "0",
            deltaQuantityUn: "-2450",
            observedDeltaUn: "-2450",
            postedQuantityUn: "1000",
            compatibleReductionUn: "1000",
            adjustedPlanningDeltaUn: "-1450",
            invoiceMatchStatus: "reconciled",
            managerialStatus: "partial_invoicing",
            residualUnexplainedUn: "1450",
            managerialExplanation:
              "Parte da redução (1000 UN) é compatível com NF MyWEG; residual de 1450 UN sem explicação fiscal.",
            portalInvoiceMaterials: [{ materialWeg: "MAT-001" }],
            portalInvoiceSources: ["obs-1"],
            remessas: [
              {
                remessa: "2026-11-12",
                previousQuantityUn: "2450",
                currentQuantityUn: "0",
                deltaQuantityUn: "-2450",
                movement: "disappeared",
              },
            ],
          },
        ],
      }),
    );

    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("col-managerial").textContent).toMatch(
        /Faturamento parcial/i,
      );
    });
    expect(screen.getByTestId("col-residual").textContent).toContain("1.450");

    fireEvent.click(screen.getByRole("button", { name: /^detalhes$/i }));
    await waitFor(() => {
      expect(screen.getByText(/residual de 1450 UN/i)).toBeTruthy();
    });
  });

  it("exibe NF zero como fato e ajuste nulo como Não disponível na tabela", async () => {
    fetchProducts.mockResolvedValue(
      portalPayload({
        totals: {
          previousQuantityUn: "2",
          currentQuantityUn: "2",
          deltaQuantityUn: "0",
          postedQuantityUn: "0",
          observedDeltaUn: "0",
          adjustedPlanningDeltaUn: null,
        },
        portalInvoices: {
          status: "complete",
          coverage: "complete",
          coveredDates: ["2026-11-06"],
          missingDates: [],
          coveredDayCount: 1,
          missingDayCount: 0,
        },
        items: [
          {
            ...basePayload.items[0],
            observedDeltaUn: "0",
            postedQuantityUn: "0",
            adjustedPlanningDeltaUn: null,
            residualUnexplainedUn: null,
            invoiceMatchStatus: "none",
            managerialStatus: "other_movement",
            portalInvoiceMaterials: [],
            portalInvoiceSources: [],
          },
        ],
      }),
    );

    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("col-posted").textContent).toContain("0");
    });
    expect(screen.getByTestId("col-residual").textContent).toContain(
      "Não disponível",
    );
  });

  it("não mostra 0 NF como fato em cobertura parcial", async () => {
    fetchProducts.mockResolvedValue(
      portalPayload({
        totals: {
          previousQuantityUn: "2",
          currentQuantityUn: "1",
          deltaQuantityUn: "-1",
          postedQuantityUn: null,
          observedDeltaUn: "-1",
          adjustedPlanningDeltaUn: null,
        },
        portalInvoices: {
          status: "partial",
          coverage: "partial",
          coveredDates: ["2026-11-06"],
          missingDates: ["2026-11-07"],
          coveredDayCount: 1,
          missingDayCount: 1,
        },
        items: [
          {
            ...basePayload.items[0],
            observedDeltaUn: "-1",
            postedQuantityUn: null,
            adjustedPlanningDeltaUn: null,
            invoiceMatchStatus: "partial_coverage",
            managerialStatus: "reconciliation_pending",
            portalInvoiceSources: ["obs-1"],
            portalInvoiceMaterials: [{ materialWeg: "MAT-001" }],
          },
        ],
      }),
    );

    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("col-posted").textContent).toContain(
        "Não disponível",
      );
    });
    expect(screen.getByTestId("col-managerial").textContent).toMatch(
      /Conciliação pendente/i,
    );
  });

  it("trata importação pendente, conflito e indisponível como conciliação pendente", async () => {
    for (const status of [
      "pending_invoice_ingestion",
      "conflict",
      "unavailable",
    ] as const) {
      cleanup();
      fetchProducts.mockResolvedValue(
        portalPayload({
          totals: {
            previousQuantityUn: "2",
            currentQuantityUn: "2",
            deltaQuantityUn: "0",
            postedQuantityUn: null,
            observedDeltaUn: "0",
            adjustedPlanningDeltaUn: null,
          },
          portalInvoices: {
            status,
            coverage: status,
            coveredDayCount: 0,
            missingDayCount: 1,
          },
          items: [
            {
              ...basePayload.items[0],
              managerialStatus: "reconciliation_pending",
              postedQuantityUn: null,
              invoiceMatchStatus:
                status === "conflict"
                  ? "conflict"
                  : status === "unavailable"
                    ? "unavailable"
                    : "partial_coverage",
            },
          ],
        }),
      );
      render(
        <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
      );
      await waitFor(() => {
        expect(screen.getByTestId("col-managerial").textContent).toMatch(
          /Conciliação pendente/i,
        );
      });
    }
  });

  it("exibe diferença observada zero com ajuste diferente de zero", async () => {
    fetchProducts.mockResolvedValue(portalPayload());
    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("col-observed").textContent).toContain("0");
    });
    expect(screen.getByTestId("col-posted").textContent).toContain("10");
  });

  it("identifica orphan e attributed_elsewhere", async () => {
    fetchProducts.mockResolvedValue(
      portalPayload({
        items: [
          {
            ...basePayload.items[0],
            productKey: "ref:MAT-ORPHAN",
            verifiedProductCode: null,
            materialWegTratado: "MAT-ORPHAN",
            portalInvoiceOrphan: true,
            observedDeltaUn: "0",
            postedQuantityUn: "3",
            adjustedPlanningDeltaUn: "3",
            invoiceMatchStatus: "reconciled",
            managerialStatus: "reconciliation_pending",
            portalInvoiceMaterials: [{ materialWeg: "MAT-ORPHAN" }],
            portalInvoiceSources: ["obs-1"],
            remessas: [],
          },
          {
            ...basePayload.items[0],
            productKey: "code:other",
            verifiedProductCode: "other",
            observedDeltaUn: "-2",
            postedQuantityUn: null,
            adjustedPlanningDeltaUn: null,
            invoiceMatchStatus: "attributed_elsewhere",
            managerialStatus: "reconciliation_pending",
            portalInvoiceMaterials: [
              {
                materialWeg: "MAT-001",
                note: "Quantidade fiscal atribuída a outra identidade do mesmo material.",
              },
            ],
            portalInvoiceSources: ["obs-1"],
          },
        ],
        total: 2,
      }),
    );

    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByText(/NF sem correspondência de necessidade/i)).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: /row-code:other/i }));
    await waitFor(() => {
      expect(
        screen.getAllByText(/atribuída a outra identidade/i).length,
      ).toBeGreaterThan(0);
    });
    expect(fetchObservationItems).not.toHaveBeenCalled();
  });

  it("carrega detalhe NF sob demanda com filtro exato e zeros à esquerda", async () => {
    fetchProducts.mockResolvedValue(
      portalPayload({
        items: [
          {
            ...basePayload.items[0],
            portalInvoiceMaterials: [
              {
                materialWeg: "MAT-001",
                postedQuantityUn: "10",
              },
            ],
            portalInvoiceSources: ["obs-1"],
          },
        ],
      }),
    );
    fetchObservationItems.mockResolvedValue({
      branch: "02",
      observationId: "obs-1",
      collectionId: "col-1",
      documentDate: "2026-11-06",
      observationStatus: "with_records",
      page: 1,
      pageSize: 50,
      total: 2,
      items: [
        {
          id: "item-1",
          sourceLineNo: 1,
          invoiceNumber: "000123",
          invoiceSeries: "1",
          materialWeg: "MAT-001",
          quantityOriginal: "10",
          sourceUnit: "UN",
          quantityUn: "10",
          unitComparability: "exact",
          departureDate: "2026-11-06",
        },
        {
          id: "item-2",
          sourceLineNo: 2,
          invoiceNumber: "000999",
          invoiceSeries: "1",
          materialWeg: "OUTRO",
          quantityOriginal: "5",
          sourceUnit: "UN",
          quantityUn: "5",
          unitComparability: "exact",
          departureDate: "2026-11-06",
        },
      ],
    });

    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    await waitFor(() => {
      expect(screen.getByTestId("products-table")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: /^detalhes$/i }));

    await waitFor(() => {
      expect(fetchObservation).toHaveBeenCalledWith(
        expect.objectContaining({ observationId: "obs-1" }),
      );
      expect(fetchObservationItems).toHaveBeenCalledWith(
        expect.objectContaining({
          observationId: "obs-1",
          search: "MAT-001",
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText("000123")).toBeTruthy();
    });
    expect(screen.queryByText("000999")).toBeNull();
  });

  it("exibe 403 sem sobrescrever com payload antigo", async () => {
    fetchProducts
      .mockResolvedValueOnce(basePayload)
      .mockRejectedValueOnce(new HttpRequestError("forbidden", 403));

    render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );
    await waitFor(() => {
      expect(screen.getByTestId("products-table")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: /Atualizar conciliação/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Sem permissão para consolidar necessidades WEG por produto/i),
      ).toBeTruthy();
    });
  });

  it("descarta resposta obsoleta quando uma consulta mais nova sobrescreve", async () => {
    let resolveFirst: (value: MyWegCompareProductsPayload) => void = () => undefined;
    const first = new Promise<MyWegCompareProductsPayload>((resolve) => {
      resolveFirst = resolve;
    });
    fetchProducts
      .mockImplementationOnce(() => first)
      .mockResolvedValueOnce(portalPayload());

    const { rerender } = render(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="" />,
    );

    rerender(
      <MyWegProductConsolidationPanel fromId="from" toId="to" search="novo" />,
    );

    await waitFor(() => {
      expect(fetchProducts).toHaveBeenCalledTimes(2);
    });

    resolveFirst(basePayload);

    await waitFor(() => {
      expect(screen.getByTestId("products-table")).toBeTruthy();
    });
    expect(screen.getByText("Diferença líquida")).toBeTruthy();
    expect(
      screen.getByText((_, node) => node?.textContent?.trim() === "0 UN"),
    ).toBeTruthy();
    expect(screen.getByTestId("col-posted").textContent).toContain("10");
  });
});
