// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { copy } from "../content/copy";
import type { PpcBranch } from "../types";
import { DemandPage } from "./DemandPage";

const MYWEG_PERMISSION = "production-control.myweg-needs.view";
const requests = vi.hoisted(() => ({
  calls: [] as Array<{ branch: string; origin: string; page: number; refresh: boolean }>,
}));

vi.mock("../api/ppcApi", () => ({
  fetchDemand: async (params: {
    branch: string;
    origin: string;
    page: number;
    refresh?: boolean;
  }) => {
    requests.calls.push({
      branch: params.branch,
      origin: params.origin,
      page: params.page,
      refresh: Boolean(params.refresh),
    });
    return {
      branch: params.branch,
      items: [],
      summary: {
        line_count: 0,
        open_quantity: 0,
        customer_count: 0,
        product_count: 0,
        late_line_count: 0,
        uncovered_quantity: 0,
        at_risk_line_count: 0,
        next_due_date: null,
        official_aggregate: true,
        by_origin: null,
      },
      horizon: [],
      filters: {
        origin: params.origin,
        statuses: [],
        customer_options: [],
      },
      pagination: {
        page: params.page,
        page_size: 50,
        total: 0,
        total_pages: 0,
        is_complete: true,
      },
      myweg: null,
    };
  },
}));

vi.mock("@delpi/plugin-ui/index", () => ({
  CHART_COLORS_DEPARTMENTAL: ["#023667", "#00a6de"],
  createDashboardKpiCard: () => ({ title }: { title: string }) => <div>{title}</div>,
  createDashboardLoadingActivityCard: () => ({ title }: { title: string }) => <div>{title}</div>,
  createDashboardStatusBadge: () => () => null,
  createDashboardMultiSelectField: () => () => null,
  multiSelectBemClasses: () => ({}),
  formFieldShellBemClasses: () => ({}),
  MultiTypeSeriesChart: () => null,
  NativeSelectField: ({
    id,
    label,
    value,
    options,
    onChange,
  }: {
    id: string;
    label: string;
    value: string;
    options: Array<{ value: string; label: string }>;
    onChange: (value: string) => void;
  }) => (
    <label htmlFor={id}>
      {label}
      <select id={id} value={value} onChange={(event) => onChange(event.currentTarget.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  ),
}));

vi.mock("../components/PpcWorkspaceHeader", () => ({
  PpcWorkspaceHeader: ({ onRefresh }: { onRefresh?: () => void }) => (
    <button type="button" onClick={onRefresh}>
      Atualizar
    </button>
  ),
}));

vi.mock("../components/dataTableUi", () => ({
  DataTableSection: ({
    toolbarExtra,
    serverPagination,
  }: {
    toolbarExtra?: ReactNode;
    serverPagination?: { onPageChange: (page: number) => void };
  }) => (
    <section data-testid="tabela-demandas">
      {toolbarExtra}
      <button type="button" onClick={() => serverPagination?.onPageChange(2)}>
        Página seguinte
      </button>
    </section>
  ),
}));

vi.mock("../components/ChartCard", () => ({
  ChartCard: ({ children }: { children?: ReactNode }) => <section>{children}</section>,
}));

vi.mock("../components/DemandDetailModal", () => ({
  DemandDetailModal: () => null,
}));

afterEach(() => {
  cleanup();
  requests.calls.length = 0;
});

function view(
  branch: PpcBranch,
  permissions: string[] = [MYWEG_PERMISSION],
  isSuperadmin = false,
) {
  // App usa a filial como chave para nao herdar um filtro da outra unidade.
  return (
    <DemandPage
      key={branch}
      branch={branch}
      search={null}
      status={null}
      permissions={permissions}
      isSuperadmin={isSuperadmin}
    />
  );
}

describe("DemandPage origem inicial #1554", () => {
  it("abre Todas na filial 02 autorizada e exibe ambas as origens", async () => {
    render(view("02"));
    const select = (await screen.findByLabelText(copy.demand.originLabel)) as HTMLSelectElement;
    expect(select.value).toBe("both");
    expect(Array.from(select.options).map((option) => option.value)).toEqual([
      "both", "protheus", "myweg",
    ]);
    expect(requests.calls[0]).toMatchObject({ branch: "02", origin: "both" });
  });

  it("ao trocar da filial 01 para a 02, troca Protheus por Todas", async () => {
    const { rerender } = render(view("01"));
    await waitFor(() => expect(requests.calls.at(-1)?.origin).toBe("protheus"));
    expect(screen.queryByLabelText(copy.demand.originLabel)).toBeNull();

    rerender(view("02"));
    const select = (await screen.findByLabelText(copy.demand.originLabel)) as HTMLSelectElement;
    expect(select.value).toBe("both");
    expect(requests.calls.at(-1)).toMatchObject({ branch: "02", origin: "both" });
  });

  it("preserva selecao manual de Protheus em paginacao e Atualizar", async () => {
    render(view("02"));
    const select = (await screen.findByLabelText(copy.demand.originLabel)) as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "protheus" } });

    await waitFor(() => expect(requests.calls.at(-1)?.origin).toBe("protheus"));
    fireEvent.click(screen.getByRole("button", { name: "Página seguinte" }));
    await waitFor(() => expect(requests.calls.at(-1)?.page).toBe(2));
    expect(requests.calls.at(-1)?.origin).toBe("protheus");

    fireEvent.click(screen.getByRole("button", { name: "Atualizar" }));
    await waitFor(() => expect(requests.calls.at(-1)?.refresh).toBe(true));
    expect(requests.calls.at(-1)?.origin).toBe("protheus");
    expect((screen.getByLabelText(copy.demand.originLabel) as HTMLSelectElement).value).toBe(
      "protheus",
    );
  });

  it("sem permissao MyWEG, consulta Protheus e esconde as opcoes restritas", async () => {
    render(view("02", ["production-control.demand.view"]));
    await waitFor(() => expect(requests.calls.at(-1)?.origin).toBe("protheus"));
    expect(screen.queryByLabelText(copy.demand.originLabel)).toBeNull();
  });

  it("superadmin sem permissao explicita abre Todas na filial 02", async () => {
    render(view("02", [], true));
    const select = (await screen.findByLabelText(copy.demand.originLabel)) as HTMLSelectElement;
    expect(select.value).toBe("both");
    expect(requests.calls[0].origin).toBe("both");
  });
});
