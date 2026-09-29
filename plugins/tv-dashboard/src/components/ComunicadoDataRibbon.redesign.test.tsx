// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  ComunicadoBlock,
  ComunicadoDataSourceBlock,
  ComunicadoKpiViewBlock,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import { buildExpressionParamValue } from "../utils/paramExpressions";

const ROUTE: TvDataRouteCatalogItem = {
  operationId: "comercial.rol.summary",
  label: "ROL por centro",
  category: "Comercial",
  valueFields: ["rol", "meta"],
  valueFieldLabels: { rol: "ROL", meta: "Meta" },
  paramSchema: {
    start_date: { type: "string", format: "date", label: "Início" },
    end_date: { type: "string", format: "date", label: "Fim" },
    branch: { type: "string", enum: ["01", "02"], label: "Filial" },
  },
};

const SUPPORT: ParamExpressionSupport = {
  enabled: true,
  loading: false,
  functions: [
    {
      name: "Date.AddMonths",
      kind: "scalar",
      signature: "Date.AddMonths(value, months) as date",
      parameters: ["value", "months"],
    },
  ],
  registryVersion: "1",
};

const SOURCE: ComunicadoDataSourceBlock = {
  id: "src-1",
  type: "data_source",
  frame: { x: 0, y: 0, w: 10, h: 5 },
  dataBinding: {
    operationId: "comercial.rol.summary",
    params: { dateRangePreset: "this_month" },
  },
};

const KPI: ComunicadoKpiViewBlock = {
  id: "kpi-1",
  type: "kpi_view",
  frame: { x: 0, y: 6, w: 10, h: 5 },
  dataSourceId: "src-1",
  kpiProjection: { metrics: [{ field: "rol", aggregation: "sum" }] },
};

type EditorStub = {
  blocks: ComunicadoBlock[];
  selected: ComunicadoBlock | null;
  selectedIds: string[];
  updateSelected: ReturnType<typeof vi.fn>;
  updateBlock: ReturnType<typeof vi.fn>;
  openDataCatalog: ReturnType<typeof vi.fn>;
  openExpressionEditor: ReturnType<typeof vi.fn>;
  setSelectionPanelTab: ReturnType<typeof vi.fn>;
  setDataPanelIntent: ReturnType<typeof vi.fn>;
  setDataPanelOpen: ReturnType<typeof vi.fn>;
  [key: string]: unknown;
};

let editorState: EditorStub;

function freshEditorState(overrides: Partial<EditorStub> = {}): EditorStub {
  return {
    blocks: [SOURCE, KPI],
    config: { dataModels: [] },
    selected: KPI,
    selectedIds: ["kpi-1"],
    selectedId: "kpi-1",
    selectedBlocks: [KPI],
    dataPanelIntent: "binding",
    updateSelected: vi.fn(),
    updateBlock: vi.fn(),
    updateBlocksAtomically: vi.fn(),
    setSelectionPanelTab: vi.fn(),
    setDataPanelIntent: vi.fn(),
    setDataPanelOpen: vi.fn(),
    openDataCatalog: vi.fn(),
    openExpressionEditor: vi.fn(),
    closeExpressionEditor: vi.fn(),
    expressionEditRequest: null,
    getDataPreviewResolved: vi.fn(() => undefined),
    reconcileTablePartsForVisibleKeys: vi.fn(),
    reconcileChartPartForSeriesFields: vi.fn(),
    saveDataModel: vi.fn(),
    globalRefreshSec: 300,
    ...overrides,
  };
}

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => editorState,
}));

vi.mock("../hooks/useTvDataRouteLabelCatalog", () => ({
  useTvDataRouteLabelCatalog: () => ({
    routes: [ROUTE],
    labelCatalog: {
      "comercial.rol.summary": { label: "ROL por centro" },
    },
  }),
}));

vi.mock("../hooks/useParamExpressionCapability", () => ({
  useParamExpressionCapability: () => SUPPORT,
}));

import { ComunicadoDataRibbon } from "./ComunicadoDataRibbon";

/** Abre select custom e clica na opção pelo texto exato ou regex. */
function chooseOption(trigger: HTMLElement, label: string | RegExp) {
  fireEvent.click(trigger);
  const option = screen
    .getAllByRole("listbox")
    .flatMap((list) => Array.from(list.querySelectorAll("button")))
    .find((button) =>
      typeof label === "string"
        ? button.textContent === label
        : label.test(button.textContent ?? ""),
    );
  expect(option, `opção ${label}`).toBeTruthy();
  fireEvent.click(option!);
}

afterEach(() => cleanup());

describe("ComunicadoDataRibbon — grupos e contexto", () => {
  it("renderiza os grupos estáveis com seleção ligada", () => {
    editorState = freshEditorState();
    render(<ComunicadoDataRibbon />);
    for (const caption of [
      "Fonte",
      "Campo",
      "Período",
      "Atualização",
      "Expressão",
      "Mais",
    ]) {
      expect(screen.getAllByText(caption).length).toBeGreaterThan(0);
    }
    // Tile de Período mostra o preset persistido.
    expect(screen.getByText("Este mês (até hoje)")).toBeTruthy();
  });

  it("sem seleção de dados, só o grupo Fonte (onboarding)", () => {
    editorState = freshEditorState({ selected: null, selectedIds: [] });
    render(<ComunicadoDataRibbon />);
    expect(screen.getByText("Inserir fonte…")).toBeTruthy();
    expect(screen.queryByText("Período")).toBeNull();
    expect(screen.queryByText("Atualização")).toBeNull();
  });

  it("fonte aparece no seletor unificado da faixa", () => {
    editorState = freshEditorState();
    render(<ComunicadoDataRibbon />);
    const sourceSelect = screen.getByRole("button", { name: "Fonte de dados" });
    expect(sourceSelect.textContent).toContain("ROL por centro");
  });
});

describe("ComunicadoDataRibbon — campo e agregação (cenário A)", () => {
  it("troca o campo do KPI pela faixa (updateSelected com projeção)", () => {
    editorState = freshEditorState();
    render(<ComunicadoDataRibbon />);
    chooseOption(screen.getByRole("button", { name: "Campo do KPI" }), "Meta");
    const patch = editorState.updateSelected.mock.calls.at(-1)![0] as {
      kpiProjection?: { metrics?: Array<{ field?: string }> };
    };
    expect(patch.kpiProjection?.metrics?.[0]?.field).toBe("meta");
  });

  it("troca a agregação direto na topbar (cenário A — topbar-only)", () => {
    editorState = freshEditorState();
    render(<ComunicadoDataRibbon />);
    const aggregations = screen.getAllByRole("button", { name: "Agregação" });
    chooseOption(aggregations[0]!, "Média");
    const patch = editorState.updateSelected.mock.calls.at(-1)![0] as {
      kpiProjection?: { metrics?: Array<{ aggregation?: string }> };
    };
    expect(patch.kpiProjection?.metrics?.[0]?.aggregation).toBe("avg");
  });
});

describe("ComunicadoDataRibbon — sincronização (cenário B)", () => {
  it("mudança de período no estado atualiza o rótulo do tile no mesmo render", () => {
    editorState = freshEditorState();
    const { rerender } = render(<ComunicadoDataRibbon />);
    expect(screen.getByText("Este mês (até hoje)")).toBeTruthy();

    // Sidebar alterou params → mesmo estado → ribbon reflete na hora.
    editorState = freshEditorState({
      blocks: [
        {
          ...SOURCE,
          dataBinding: {
            ...SOURCE.dataBinding,
            params: { dateRangePreset: "last_30_days" },
          },
        },
        KPI,
      ],
    });
    rerender(<ComunicadoDataRibbon />);
    expect(screen.getByText("Últimos 30 dias")).toBeTruthy();
    expect(screen.queryByText("Este mês (até hoje)")).toBeNull();
  });
});

describe("ComunicadoDataRibbon — expressão (cenários C/D)", () => {
  it("flyout Expressão lista params elegíveis e abre o drawer request", () => {
    editorState = freshEditorState();
    render(<ComunicadoDataRibbon />);
    // Abre o tile «Expressão» do grupo (o primeiro é o tile real; demais
    // são o trigger de medida/colapso do grupo no harness de teste).
    fireEvent.click(screen.getAllByRole("button", { name: "Expressão" })[0]!);
    // Params elegíveis: start_date, end_date, branch.
    expect(screen.getAllByText(/Nova expressão/).length).toBe(3);
    fireEvent.click(screen.getAllByText(/Nova expressão/)[0]!);
    expect(editorState.openExpressionEditor).toHaveBeenCalledTimes(1);
    const request = editorState.openExpressionEditor.mock.calls[0]![0] as {
      paramKey: string;
      paramLabel: string;
      spec: unknown;
      previewBlockId?: string | null;
      apply: (spec: never) => void;
    };
    expect(request.paramKey).toBe("start_date");
    expect(request.previewBlockId).toBe("src-1");
    // Draft inicial: hoje (identifier) para param de data.
    expect(request.spec).toEqual(
      buildExpressionParamValue({ kind: "identifier", value: "today" }),
    );
  });

  it("parâmetro com expressão persistida mostra o cartão-resumo no flyout", () => {
    const expr = buildExpressionParamValue({ kind: "identifier", value: "today" });
    editorState = freshEditorState({
      blocks: [
        {
          ...SOURCE,
          dataBinding: {
            ...SOURCE.dataBinding,
            params: { dateRangePreset: "this_month", start_date: expr },
          },
        },
        KPI,
      ],
    });
    render(<ComunicadoDataRibbon />);
    // Tile conta a expressão ativa.
    expect(screen.getByText("Expressão (1)")).toBeTruthy();
    fireEvent.click(screen.getAllByRole("button", { name: "Expressão (1)" })[0]!);
    // Cartão-resumo (não o editor inline) + «Editar expressão».
    expect(document.querySelector(".td-expression-summary")).toBeTruthy();
    expect(screen.getByText("Editar expressão")).toBeTruthy();
    fireEvent.click(screen.getByText("Editar expressão"));
    const request = editorState.openExpressionEditor.mock.calls.at(-1)![0] as {
      paramKey: string;
      spec: unknown;
    };
    // AST vai intacto para o drawer — nunca reescrito em label.
    expect(request.paramKey).toBe("start_date");
    expect(request.spec).toEqual(expr);
  });
});
