// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { LineFeederMaterialsPreviewPayload } from "../types";
import { LineFeederMaterialsPanel } from "./LineFeederMaterialsPanel";

vi.mock("@delpi/plugin-ui/index", () => ({
  createDashboardKpiCard: () =>
    function Kpi({ title, value }: { title: string; value: string }) {
      return (
        <div>
          <span>{title}</span>
          <strong>{value}</strong>
        </div>
      );
    },
  createDashboardStatusBadge: () =>
    function Badge({ label }: { label: string }) {
      return <span>{label}</span>;
    },
}));

vi.mock("./dataTableUi", () => ({
  DataTableSection: ({
    rows,
    emptyMessage,
    onRowClick,
    renderCard,
  }: {
    rows: Array<{ product_code: string; to_collect_qty: number | null; unit: string }>;
    emptyMessage: string;
    onRowClick?: (row: { product_code: string }) => void;
    renderCard?: (row: {
      product_code: string;
      to_collect_qty: number | null;
      unit: string;
      required_qty: number;
      factory_available_qty: number | null;
      status: string;
    }) => React.ReactNode;
  }) => (
    <div>
      {rows.length === 0 ? <p>{emptyMessage}</p> : null}
      {rows.map((row) => (
        <button
          key={row.product_code}
          type="button"
          onClick={() => onRowClick?.(row)}
        >
          {renderCard
            ? renderCard(row as never)
            : `${row.product_code}:${row.to_collect_qty}`}
        </button>
      ))}
    </div>
  ),
}));

function basePayload(
  partial: Partial<LineFeederMaterialsPreviewPayload> = {},
): LineFeederMaterialsPreviewPayload {
  return {
    branch: "01",
    hours_per_work_center: 3,
    publication: {
      generation_id: "g1",
      publication_revision: "1",
      published_at: null,
      published_by: null,
      source_refreshed_at: null,
      start_date: null,
      end_date: null,
    },
    preview_completeness: "complete",
    operational_list_safe: true,
    stop_reasons: [],
    demand_warnings: [],
    horizon: { covered_operation_count: 2, work_centers: [] },
    summary: {
      material_count: 2,
      covered_count: 1,
      to_pick_count: 1,
      at_risk_count: 0,
      unknown_count: 0,
      to_collect_qty: 60,
    },
    materials: [
      {
        product_code: "MP-001",
        description: "Cabo elétrico",
        unit: "M",
        required_qty: 100,
        factory_available_qty: 40,
        to_collect_qty: 60,
        source_available_qty: 200,
        status: "to_pick",
        work_centers: ["CT-A", "CT-B"],
        origins: [
          {
            work_center: "CT-A",
            production_order: "OP1",
            operation_code: "01",
            operation_id: "id-1",
            sequence_position: 1,
            covered_qty: 10,
            pending_qty: 10,
            open_qty: 50,
            fraction: 1,
            required_qty: 50,
            pa_product_code: "90262910",
          },
          {
            work_center: "CT-B",
            production_order: "OP2",
            operation_code: "01",
            operation_id: "id-2",
            sequence_position: 1,
            covered_qty: 10,
            pending_qty: 10,
            open_qty: 50,
            fraction: 1,
            required_qty: 50,
            pa_product_code: "90262911",
          },
        ],
      },
      {
        product_code: "MP-002",
        description: "Parafuso",
        unit: "PC",
        required_qty: 10,
        factory_available_qty: 10,
        to_collect_qty: 0,
        source_available_qty: 0,
        status: "covered",
        work_centers: ["CT-A"],
        origins: [],
      },
    ],
    ...partial,
  };
}

afterEach(() => {
  cleanup();
});

describe("LineFeederMaterialsPanel", () => {
  it("destaca coleta 60 e permite ver origens de vários CTs", () => {
    render(
      <LineFeederMaterialsPanel
        data={basePayload()}
        query={{ workCenters: ["CT-A", "CT-B"], hoursPerWorkCenter: 3 }}
      />,
    );
    expect(screen.getByText(/Coletar:.*60/i)).toBeTruthy();
    expect(screen.getByText(/^CT:\s*CT-A$/i)).toBeTruthy();
    fireEvent.click(screen.getByText(/MP-001/i).closest("button")!);
    expect(screen.getByText(/CT-A · OP OP1 · 90262910/)).toBeTruthy();
    expect(screen.getByText(/CT-B · OP OP2 · 90262911/)).toBeTruthy();
    expect(screen.queryByText(/Op\./)).toBeNull();
  });


  it("identifica empenho de OP sem operação e não inventa um CT de destino", () => {
    const source = basePayload().materials[0];
    const data = basePayload({
      materials: [
        {
          ...source,
          work_centers: [],
          origins: [
            {
              ...source.origins[0],
              operation_id: "order-level:OP1",
              work_center: "",
              operation_code: "",
              covered_qty: 0,
              pending_qty: 0,
              fraction: 0,
            },
          ],
        },
      ],
    });
    render(
      <LineFeederMaterialsPanel
        data={data}
        query={{ workCenters: ["CT-A", "CT-B"], hoursPerWorkCenter: 3 }}
      />,
    );
    expect(screen.getByText(/Sem CT definido/i)).toBeTruthy();
    expect(screen.getByText(/Confirme com o PCP o posto de entrega/i)).toBeTruthy();
    fireEvent.click(screen.getByText(/MP-001/i).closest("button")!);
    expect(screen.getByText(/OP OP1 · empenho sem operação definida/i)).toBeTruthy();
  });

  it("avisa quando operações de outra filial foram excluídas", () => {
    const baseline = basePayload();
    render(
      <LineFeederMaterialsPanel
        data={basePayload({
          publication: {
            ...baseline.publication,
            foreign_branch_operations_excluded: 1,
          },
        })}
        query={{ workCenters: ["CT-A"], hoursPerWorkCenter: 2 }}
      />,
    );
    expect(screen.getByText(/operação de outra filial foi desconsiderada/i)).toBeTruthy();
    expect(screen.getByText(/Solicite ao PCP que atualize e republique/i)).toBeTruthy();
    expect(screen.getByText(/MP-001/)).toBeTruthy();
  });

  it("não apresenta lista operacional quando operational_list_safe=false", () => {
    render(
      <LineFeederMaterialsPanel
        data={basePayload({
          operational_list_safe: false,
          preview_completeness: "incomplete",
          stop_reasons: ["commitments_incomplete"],
        })}
        query={{ workCenters: ["CT-A"], hoursPerWorkCenter: 2 }}
      />,
    );
    expect(screen.getByText(/Prévia incompleta/i)).toBeTruthy();
    expect(screen.queryByText(/Coletar:.*60/i)).toBeNull();
  });

  it("exibe diagnóstico específico do CT sem perder a orientação de nova consulta", () => {
    render(
      <LineFeederMaterialsPanel
        data={basePayload({
          operational_list_safe: false,
          preview_completeness: "incomplete",
          stop_reasons: ["horizon_incomplete"],
          diagnostics: [
            {
              work_center: "012",
              stop_reason: "standard_time_unavailable",
              production_order: "OP9",
              operation_code: "01",
              message:
                "Não foi possível calcular o horizonte do CT 012 porque uma operação está sem tempo padrão válido. Verifique o cadastro da operação.",
            },
          ],
          materials: [],
        })}
        query={{ workCenters: ["012"], hoursPerWorkCenter: 8 }}
      />,
    );
    expect(screen.getByText(/sem tempo padrão válido/i)).toBeTruthy();
    expect(screen.getByText(/seleção de postos e horas foi mantida/i)).toBeTruthy();
    expect(screen.queryByText(/Coletar:.*60/i)).toBeNull();
  });

  it("mensagem adequada quando não há empenhos", () => {
    render(
      <LineFeederMaterialsPanel
        data={basePayload({
          materials: [],
          summary: {
            material_count: 0,
            covered_count: 0,
            to_pick_count: 0,
            at_risk_count: 0,
            unknown_count: 0,
            to_collect_qty: 0,
          },
          demand_warnings: [{ code: "no_commitments" }],
        })}
        query={{ workCenters: ["CT-A"], hoursPerWorkCenter: 1 }}
      />,
    );
    expect(screen.getByText(/Não há matérias-primas ativas/i)).toBeTruthy();
  });
});
