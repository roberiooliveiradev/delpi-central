// @vitest-environment happy-dom
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Filter, Sigma } from "lucide-react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  DELPI_UI_OVERLAY_Z_INDEX,
  resetExclusiveAnchoredPanelForTests,
} from "@delpi/plugin-ui/index";
import type { ComunicadoDataSourceBlock } from "@delpi/tv-dashboard-presentation";

import type { Slide, TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import type { DataRibbonModel } from "../hooks/useDataRibbonModel";
import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import { buildExpressionParamValue } from "../utils/paramExpressions";
import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import { useComunicadoEditor } from "./comunicadoEditorContextCore";
import { DataRibbonExpressionFlyout } from "./DataRibbonControls";
import { DeckRibbonTilePopover } from "./deck/DeckRibbonTilePopover";
import { ExpressionEditorModalHost } from "./ExpressionEditorModalHost";
import { PlaylistDataFiltersFields } from "./PlaylistDataFiltersFields";

const ROUTE: TvDataRouteCatalogItem = {
  operationId: "comercial.rol.summary",
  label: "ROL por centro",
  category: "Comercial",
  valueFields: ["rol"],
  paramSchema: {
    start_date: { type: "string", format: "date", label: "Início" },
    end_date: { type: "string", format: "date", label: "Fim" },
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

const EXPR = buildExpressionParamValue({ kind: "identifier", value: "today" });

const SOURCE: ComunicadoDataSourceBlock = {
  id: "src-1",
  type: "data_source",
  frame: { x: 0, y: 0, w: 10, h: 5 },
  dataBinding: { operationId: ROUTE.operationId, params: {} },
};

const SLIDES = [
  { id: "s1", nativeConfig: { version: 2, blocks: [SOURCE] } },
] as unknown as Slide[];

vi.mock("../api/tvDashboardApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/tvDashboardApi")>();
  return {
    ...actual,
    listPlaylistMedia: vi.fn(async () => []),
    listDataRoutes: vi.fn(async () => [ROUTE]),
  };
});

vi.mock("../hooks/useTvDataRouteLabelCatalog", () => ({
  useTvDataRouteLabelCatalog: () => ({ routes: [ROUTE], labelCatalog: {} }),
}));

vi.mock("../hooks/useParamExpressionCapability", () => ({
  useParamExpressionCapability: () => SUPPORT,
}));

function ribbonModel(): DataRibbonModel {
  return {
    bindingTarget: SOURCE,
    bindingModel: null,
    params: {},
    paramSchema: ROUTE.paramSchema,
    expressionParams: [
      {
        key: "start_date",
        field: ROUTE.paramSchema!.start_date,
        label: "Início",
        expectedReturnTypes: null,
      },
    ],
    resolved: undefined,
    updateParams: vi.fn(),
  } as unknown as DataRibbonModel;
}

function OpenWithoutPopoverButton() {
  const { openExpressionEditor } = useComunicadoEditor();
  return (
    <button
      type="button"
      onClick={() =>
        openExpressionEditor({
          paramKey: "start_date",
          paramLabel: "Início",
          spec: EXPR,
          apply: vi.fn(),
        })
      }
    >
      Abrir sem popover
    </button>
  );
}

function renderEditor() {
  return render(
    <div className="dashboard-tv-dashboard">
      <ComunicadoEditorProvider
        playlistId="pl-1"
        slideId="s1"
        value={{ version: 2, blocks: [] }}
        onChange={() => {}}
      >
        <DeckRibbonTilePopover icon={Sigma} label="Expressão" panelLabel="Expressões do elemento">
          <DataRibbonExpressionFlyout model={ribbonModel()} />
        </DeckRibbonTilePopover>
        <DeckRibbonTilePopover icon={Filter} label="Filtros" panelLabel="Filtros da programação">
          <PlaylistDataFiltersFields slides={SLIDES} values={{ start_date: EXPR }} onChange={vi.fn()} />
        </DeckRibbonTilePopover>
        <OpenWithoutPopoverButton />
        <ExpressionEditorModalHost />
      </ComunicadoEditorProvider>
    </div>,
  );
}

function expressionModal() {
  return screen.queryByRole("dialog", { name: /^Expressão — / });
}

function assertSingleContainedModal() {
  const modal = expressionModal();
  expect(modal).toBeTruthy();
  expect(screen.getAllByRole("dialog")).toHaveLength(1);
  expect(modal!.getAttribute("aria-modal")).toBe("true");
  expect(modal!.closest('[data-modal-contained="true"]')).toBeTruthy();
  expect(modal!.closest(".dashboard-tv-dashboard")).toBeTruthy();
  expect(document.querySelector(".delpi-ui-drawer")).toBeNull();
}

beforeEach(() => resetExclusiveAnchoredPanelForTests());
afterEach(() => {
  cleanup();
  resetExclusiveAnchoredPanelForTests();
});

describe("Expressão — handoff popover → modal", () => {
  it("ribbon «Expressão»: o popover de origem fecha e só o modal fica ativo", async () => {
    renderEditor();
    fireEvent.click(screen.getAllByRole("button", { name: "Expressão" })[0]!);
    expect(screen.getByRole("dialog", { name: "Expressões do elemento" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Nova expressão/ }));

    await waitFor(() => expect(expressionModal()).toBeTruthy());
    expect(screen.queryByRole("dialog", { name: "Expressões do elemento" })).toBeNull();
    assertSingleContainedModal();
  });

  it("sibling — Programação › Filtros «Editar expressão» usa o mesmo handoff", async () => {
    renderEditor();
    fireEvent.click(screen.getAllByRole("button", { name: "Filtros" })[0]!);
    expect(screen.getByRole("dialog", { name: "Filtros da programação" })).toBeTruthy();

    fireEvent.click(await screen.findByRole("button", { name: /Editar expressão/ }));

    await waitFor(() => expect(expressionModal()).toBeTruthy());
    expect(screen.queryByRole("dialog", { name: "Filtros da programação" })).toBeNull();
    assertSingleContainedModal();
  });

  it("negativo — sem popover ativo o modal abre normalmente", async () => {
    renderEditor();
    expect(screen.queryAllByRole("dialog")).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Abrir sem popover" }));

    await waitFor(() => expect(expressionModal()).toBeTruthy());
    assertSingleContainedModal();
  });

  it("select dentro do modal abre acima dele e não fecha o modal", async () => {
    renderEditor();
    fireEvent.click(screen.getByRole("button", { name: "Abrir sem popover" }));
    await waitFor(() => expect(expressionModal()).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "Tipo do nó" }));
    const listbox = await screen.findByRole("listbox");
    expect(expressionModal()!.contains(listbox)).toBe(false);
    expect(DELPI_UI_OVERLAY_Z_INDEX.anchoredPanel).toBeGreaterThan(DELPI_UI_OVERLAY_Z_INDEX.modal);

    const option = Array.from(listbox.querySelectorAll("button")).find(
      (button) => button.getAttribute("aria-selected") !== "true",
    );
    expect(option).toBeTruthy();
    await act(async () => {
      fireEvent.click(option!);
    });
    expect(expressionModal()).toBeTruthy();
    expect(screen.queryByRole("listbox")).toBeNull();
  });
});
