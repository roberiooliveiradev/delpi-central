/** @vitest-environment jsdom */
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HttpRequestError } from "../api/httpClient";
import { createReport, deleteReport, getReport, listReports, updateReport } from "../api/metallographicReportsApi";
import { displayDateToIso, formatBusinessDate } from "../domain/reportForm";
import type { ReportSnapshot } from "../domain/reportForm";
import { CropDialog } from "./CropDialog";
import { MetallographicWorkspace } from "./MetallographicWorkspace";

vi.mock("@delpi/plugin-ui/index", async () => {
  const viewport = await import("../../../plugin-ui/src/components/feedback/containedModalViewport");
  const hook = await import("../../../plugin-ui/src/components/feedback/useContainedModalViewportStyle");
  return {
    printDelpiDocumentHtml: () => true,
    lockContainedModalScroll: viewport.lockContainedModalScroll,
    useContainedModalViewportStyle: hook.useContainedModalViewportStyle,
  };
});

vi.mock("../api/metallographicReportsApi", () => ({
  listReports: vi.fn(),
  getReport: vi.fn(),
  deleteReport: vi.fn(),
  createReport: vi.fn(),
  updateReport: vi.fn(),
  putImage: vi.fn(),
  getImage: vi.fn(),
  exportPdf: vi.fn(),
}));

const REPORT_ID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";

function report(): ReportSnapshot {
  return {
    id: REPORT_ID,
    report_number: "MET-2026-000007",
    report_date: "2026-10-22",
    revision: "00",
    sample: {
      terminal_code: "T-7",
      terminal_part_number: null,
      product_harness: null,
      cable: null,
      conductor_section: null,
      applicator_tool: null,
      press_equipment: null,
      batch_production_order: null,
      sample_identification: null,
    },
    measurements: {
      crimp_height_ch: { criterion: null, measured: null },
      crimp_width_cb: { criterion: null, measured: null },
      void_area_av: { criterion: null, measured: null },
      left_burr_gh_e: { criterion: null, measured: null },
      right_burr_gh_d: { criterion: null, measured: null },
    },
    conclusion: { result: null, notes: null },
    analyst: { name: null, user_id: null },
    images: {
      original: { present: false, content_type: null, sha256: null },
      measured: { present: false, content_type: null, sha256: null },
    },
    status: "draft",
    version: 3,
    created_at: "2026-10-22T10:00:00Z",
    updated_at: "2026-10-22T10:00:00Z",
  };
}

function mount(editing = false) {
  const content = document.createElement("div");
  content.className = "content";
  Object.defineProperty(content, "clientHeight", { configurable: true, value: 480 });
  content.getBoundingClientRect = () =>
    ({
      top: 12,
      left: 16,
      width: 320,
      height: 480,
      right: 336,
      bottom: 492,
      x: 16,
      y: 12,
      toJSON() {
        return {};
      },
    }) as DOMRect;
  const holder = document.createElement("div");
  content.appendChild(holder);
  document.body.appendChild(content);
  const root = createRoot(holder);
  act(() => {
    root.render(
      <MetallographicWorkspace
        editing={editing}
        reportId={editing ? REPORT_ID : undefined}
        permissions={[
          "metalography.view",
          "metalography.create",
          "metalography.edit",
          "metalography.delete",
          "metalography.export",
        ]}
      />,
    );
  });
  return { root, content };
}

describe("diálogos do metalografia", () => {
  let root: Root | undefined;

  beforeEach(() => {
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    vi.mocked(listReports).mockResolvedValue({
      data: { items: [report()], page: 1, page_size: 100, total: 1, has_next: false },
      etag: null,
      operationId: null,
    });
    vi.mocked(getReport).mockResolvedValue({ data: report(), etag: '"3"', operationId: null });
    vi.mocked(deleteReport).mockResolvedValue({
      data: { id: REPORT_ID, deleted: true, version: 4 },
      etag: null,
      operationId: null,
    });
    vi.mocked(createReport).mockResolvedValue({ data: report(), etag: '"1"', operationId: null });
    class ResizeObserverStub {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    vi.stubGlobal("ResizeObserver", ResizeObserverStub);
  });

  afterEach(() => {
    act(() => root?.unmount());
    root = undefined;
    document.body.innerHTML = "";
    vi.clearAllMocks();
  });

  async function openDelete() {
    const view = mount();
    root = view.root;
    await act(async () => {
      await Promise.resolve();
    });
    const button = document.querySelector<HTMLButtonElement>(".report-delete");
    expect(button).toBeTruthy();
    await act(async () => {
      button?.click();
    });
    return document.querySelector<HTMLElement>(".return-home-modal.open");
  }

  it("mantém o modal de exclusão aberto depois do clique, do scroll e do resize", async () => {
    const modal = await openDelete();
    expect(modal?.textContent).toContain("MET-2026-000007");
    expect(modal?.getAttribute("style") ?? "").not.toMatch(/inset:\s*auto/i);
    expect(modal?.style.top).toBe("12px");
    expect(modal?.style.left).toBe("16px");
    expect(modal?.style.width).toBe("320px");
    expect(modal?.style.height).toBe("480px");
    expect(document.activeElement?.id).toBe("delete-report-cancel");

    window.dispatchEvent(new Event("scroll"));
    window.dispatchEvent(new Event("resize"));
    modal?.querySelector("#delete-report-title")?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    modal?.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));

    expect(document.querySelector(".return-home-modal.open")).toBe(modal);
    expect(deleteReport).not.toHaveBeenCalled();
  });

  it("cancelar a exclusão não chama a API e confirmar chama uma vez", async () => {
    const modal = await openDelete();
    await act(async () => {
      modal?.querySelector<HTMLButtonElement>("#delete-report-cancel")?.click();
    });
    expect(document.querySelector(".return-home-modal.open")).toBeNull();
    expect(deleteReport).not.toHaveBeenCalled();

    const again = await openDelete();
    let release: () => void = () => {};
    vi.mocked(deleteReport).mockImplementation(
      () => new Promise((resolve) => {
        release = () => resolve({ data: { id: REPORT_ID, deleted: true, version: 4 }, etag: null, operationId: null });
      }),
    );
    const confirm = again?.querySelector<HTMLButtonElement>("#delete-report-confirm");
    await act(async () => {
      confirm?.click();
      confirm?.click();
    });
    expect(deleteReport).toHaveBeenCalledTimes(1);
    await act(async () => {
      release();
      await Promise.resolve();
    });
    expect(document.querySelector(".return-home-modal.open")).toBeNull();
  });

  it("preserva o diálogo quando a exclusão falha", async () => {
    const modal = await openDelete();
    vi.mocked(deleteReport).mockRejectedValue(new HttpRequestError("Relatório em uso.", 409));
    await act(async () => {
      modal?.querySelector<HTMLButtonElement>("#delete-report-confirm")?.click();
      await Promise.resolve();
    });
    expect(document.querySelector(".return-home-modal.open")).toBe(modal);
    expect(document.getElementById("delete-report-error")?.textContent).toContain("Relatório em uso.");
  });

  it("mantém a cópia aberta até a confirmação e não duplica o envio", async () => {
    const view = mount();
    root = view.root;
    await act(async () => {
      await Promise.resolve();
    });
    await act(async () => {
      document.querySelector<HTMLButtonElement>(".report-copy")?.click();
    });
    const modal = document.querySelector<HTMLElement>(".return-home-modal.open");
    expect(modal?.textContent).toContain("MET-2026-000007");
    modal?.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(document.querySelector(".return-home-modal.open")).toBe(modal);

    let release: () => void = () => {};
    vi.mocked(createReport).mockImplementation(
      () => new Promise((resolve) => {
        release = () => resolve({ data: report(), etag: '"1"', operationId: null });
      }),
    );
    const confirm = modal?.querySelector<HTMLButtonElement>("#copy-report-confirm");
    await act(async () => {
      confirm?.click();
      confirm?.click();
    });
    expect(createReport).toHaveBeenCalledTimes(1);
    await act(async () => {
      release();
      await Promise.resolve();
    });
  });

  it("o aviso de saída sem salvar não descarta o texto ao cancelar", async () => {
    const view = mount();
    root = view.root;
    await act(async () => {
      await Promise.resolve();
    });
    const analyst = document.getElementById("analyst") as HTMLInputElement;
    const nativeSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    await act(async () => {
      nativeSetter?.call(analyst, "Ana ainda não salva");
      analyst.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      document.querySelector<HTMLButtonElement>(".toolbar-back")?.click();
    });
    const modal = document.querySelector<HTMLElement>(".return-home-modal.open");
    expect(modal?.textContent).toContain("alterações que ainda não foram salvas");
    await act(async () => {
      modal?.querySelector<HTMLButtonElement>("#return-home-cancel")?.click();
    });
    expect(document.querySelector(".return-home-modal.open")).toBeNull();
    expect((document.getElementById("analyst") as HTMLInputElement).value).toBe("Ana ainda não salva");
    expect(updateReport).not.toHaveBeenCalled();
  });

  it("envia a data de negócio ao criar e não herda a data antiga na cópia", async () => {
    const legacy = report();
    legacy.report_date = "2020-01-15";
    vi.mocked(listReports).mockResolvedValue({
      data: { items: [legacy], page: 1, page_size: 100, total: 1, has_next: false },
      etag: null,
      operationId: null,
    });
    const today = displayDateToIso(formatBusinessDate(new Date()));
    const view = mount();
    root = view.root;
    await act(async () => {
      await Promise.resolve();
    });
    await act(async () => {
      document.querySelector<HTMLButtonElement>(".home-new")?.click();
      await Promise.resolve();
    });
    expect(createReport).toHaveBeenCalledTimes(1);
    expect(vi.mocked(createReport).mock.calls[0]?.[0].report_date).toBe(today);

    vi.mocked(createReport).mockClear();
    await act(async () => {
      document.querySelector<HTMLButtonElement>(".report-copy")?.click();
    });
    await act(async () => {
      document.querySelector<HTMLButtonElement>("#copy-report-confirm")?.click();
      await Promise.resolve();
    });
    expect(createReport).toHaveBeenCalledTimes(1);
    expect(vi.mocked(createReport).mock.calls[0]?.[0].report_date).toBe(today);
    expect(vi.mocked(createReport).mock.calls[0]?.[0].report_date).not.toBe("2020-01-15");
    expect(vi.mocked(createReport).mock.calls[0]?.[0].sample.terminal_code).toBe("T-7");
  });

  it("o recorte permanece aberto no miolo e fecha no Escape ou no fundo", () => {
    const onCancel = vi.fn();
    const holder = document.createElement("div");
    document.body.appendChild(holder);
    const local = createRoot(holder);
    act(() => {
      local.render(
        <CropDialog
          open
          title="Ajustar micrografia"
          image={null}
          box={{ position: "fixed", top: 12, left: 16, width: 320, height: 480, right: "auto", bottom: "auto" }}
          onCancel={onCancel}
          onApply={() => undefined}
        />,
      );
    });
    const modal = document.querySelector<HTMLElement>(".crop-modal.open");
    expect(modal?.style.top).toBe("12px");
    expect(modal?.getAttribute("style") ?? "").not.toMatch(/inset:\s*auto/i);
    modal?.querySelector(".crop-panel")?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(onCancel).not.toHaveBeenCalled();
    modal?.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    expect(onCancel).toHaveBeenCalledTimes(1);
    act(() => local.unmount());
  });
});
