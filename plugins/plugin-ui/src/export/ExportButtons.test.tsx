import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";

import {
  DocumentExportActions,
  ExcelExportButton,
  TabularExportButtons,
} from "./ExportButtons";
import { tableExportPayloadFromMatrix } from "./matrixAdapter";

afterEach(() => {
  cleanup();
});

describe("TabularExportButtons", () => {
  it("dispara onExport por formato", () => {
    const onExport = vi.fn();
    render(
      <TabularExportButtons
        className="dc-export-actions"
        buttonClassName="dc-ghost-btn"
        onExport={onExport}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Baixar CSV" }));
    fireEvent.click(screen.getByRole("button", { name: "Baixar Excel" }));
    fireEvent.click(screen.getByRole("button", { name: "Baixar PDF" }));

    expect(onExport).toHaveBeenCalledWith("csv");
    expect(onExport).toHaveBeenCalledWith("xlsx");
    expect(onExport).toHaveBeenCalledWith("pdf");
  });
});

describe("DocumentExportActions", () => {
  it("expõe Excel e PDF com estado exporting", () => {
    const onExportExcel = vi.fn();
    render(
      <DocumentExportActions
        exporting
        onExportExcel={onExportExcel}
        onExportPdf={() => undefined}
      />,
    );

    const group = screen.getByRole("group", { name: "Exportar documento" });
    const busy = within(group).getByRole("button", { name: /Exportando/i });
    expect(busy).toHaveProperty("disabled", true);
  });
});

describe("ExcelExportButton", () => {
  it("chama onExport", () => {
    const onExport = vi.fn();
    render(<ExcelExportButton onExport={onExport} />);
    const group = screen.getByRole("group", { name: "Exportar Excel" });
    fireEvent.click(within(group).getByRole("button", { name: /Excel/i }));
    expect(onExport).toHaveBeenCalled();
  });
});

describe("tableExportPayloadFromMatrix", () => {
  it("mapeia headers/rows para columns/records", () => {
    const payload = tableExportPayloadFromMatrix({
      title: "OEE",
      headers: ["Recurso", "Valor"],
      rows: [
        ["LN-01", 10],
        ["LN-02", 20],
      ],
    });

    expect(payload.columns).toEqual([
      { key: "c0", label: "Recurso" },
      { key: "c1", label: "Valor" },
    ]);
    expect(payload.rows[0]).toEqual({ c0: "LN-01", c1: 10 });
    expect(payload.title).toBe("OEE");
  });
});
