import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("./DataBuilderChatPanel", () => ({
  DataBuilderChatPanel: () => <div data-testid="data-builder-chat">assistente</div>,
}));

vi.mock("./ui/Modal", () => ({
  HostContainedModal: ({
    open,
    title,
    onClose,
    closeAriaLabel,
    className,
    children,
  }: {
    open: boolean;
    title: string;
    onClose: () => void;
    closeAriaLabel?: string;
    className?: string;
    children: ReactNode;
  }) => {
    if (!open) return null;
    return (
      <div data-modal-contained="true">
        <div className={className} role="dialog" aria-label={title}>
          <h2>{title}</h2>
          <button type="button" aria-label={closeAriaLabel ?? "Fechar"} onClick={onClose}>
            ×
          </button>
          <div>{children}</div>
        </div>
      </div>
    );
  },
}));

const setDataCatalogModalOpen = vi.fn();
const setDataCatalogMode = vi.fn();
const setDataCatalogAnchor = vi.fn();
const setDataPanelIntent = vi.fn();

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => ({
    dataCatalogModalOpen: true,
    setDataCatalogModalOpen,
    dataCatalogMode: "insert" as const,
    setDataCatalogMode,
    setDataCatalogAnchor,
    setDataPanelIntent,
  }),
}));

import { DataCatalogModalHost } from "./DataCatalogModalHost";

describe("DataCatalogModalHost (modal host-contained)", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renderiza modal do assistente de dados", () => {
    render(<DataCatalogModalHost />);

    const dialog = document.querySelector(".td-modal--data-catalog");
    expect(dialog).toBeTruthy();
    expect(dialog?.getAttribute("role")).toBe("dialog");
    expect(dialog?.getAttribute("aria-label")).toBe("Assistente de dados");
    expect(screen.getByTestId("data-builder-chat")).toBeTruthy();
    expect(document.querySelector('[data-modal-contained="true"]')).toBeTruthy();
  });

  it("fecha pelo botão Fechar e limpa âncora/modo", () => {
    render(<DataCatalogModalHost />);

    fireEvent.click(screen.getByLabelText("Fechar assistente"));

    expect(setDataCatalogModalOpen).toHaveBeenCalledWith(false);
    expect(setDataCatalogMode).toHaveBeenCalledWith("insert");
    expect(setDataCatalogAnchor).toHaveBeenCalledWith(null);
  });

  it("usa HostContainedModal do plugin-ui (não AnchoredPanelPortal)", async () => {
    const { readFileSync } = await import("node:fs");
    const { dirname, join } = await import("node:path");
    const { fileURLToPath } = await import("node:url");
    const source = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "DataCatalogModalHost.tsx"),
      "utf8",
    );
    expect(source).toContain("HostContainedModal");
    expect(source).not.toContain("AnchoredPanelPortal");
  });
});
