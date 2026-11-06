// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { MyWegCompareProductsPayload } from "../types";
import { MyWegProductConsolidationPanel } from "./MyWegProductConsolidationPanel";

const fetchProducts = vi.fn();

vi.mock("@delpi/plugin-ui/index", () => ({
  HelpTooltip: () => null,
}));

vi.mock("../api/ppcApi", () => ({
  fetchMyWegNeedBatchesCompareProducts: (...args: unknown[]) => fetchProducts(...args),
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
        <div key={row.productKey}>
          <button type="button" onClick={() => onRowClick?.(row)}>
            row-{row.productKey}
          </button>
          {columns
            .filter((column) => column.key === "details")
            .map((column) => (
              <div key={`${row.productKey}-details`}>{column.render(row)}</div>
            ))}
        </div>
      ))}
    </div>
  ),
}));

const payload: MyWegCompareProductsPayload = {
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
    collectedAt: "2026-11-04T08:00:00-03:00",
    collectionDate: "2026-11-04",
    importedAt: "2026-11-04T08:00:00-03:00",
    recordCount: 2,
    totals: { quantidade_original_un: "2", quantidade_mi: "0" },
  },
  toBatch: {
    id: "to",
    collectionId: "c2",
    branch: "02",
    status: "accepted",
    collectedAt: "2026-11-05T08:00:00-03:00",
    collectionDate: "2026-11-05",
    importedAt: "2026-11-05T08:00:00-03:00",
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
  totals: {
    previousQuantityUn: "2",
    currentQuantityUn: "2",
    deltaQuantityUn: "0",
  },
  items: [
    {
      productKey: "code:80016354",
      identityKind: "verified_code",
      identityConfirmed: true,
      identityReliable: true,
      verifiedProductCode: "80016354",
      previousQuantityUn: "2",
      currentQuantityUn: "2",
      deltaQuantityUn: "0",
      percentChange: "0",
      previousRemessaCount: 1,
      currentRemessaCount: 1,
      hasRemessaChanges: true,
      situation: "stable_with_date_changes",
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

describe("MyWegProductConsolidationPanel", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    fetchProducts.mockReset();
    fetchProducts.mockResolvedValue(payload);
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

    const dialog = screen.getByRole("dialog", { name: /Detalhe · 80016354/i });
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
});
