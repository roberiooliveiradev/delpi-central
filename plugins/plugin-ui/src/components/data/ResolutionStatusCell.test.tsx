import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DataTable, dataTableBemClasses } from "./DataTable";
import {
  ResolutionStatusCell,
  createDashboardResolutionStatusCell,
  formatResolutionDate,
  resolutionStatusCellBemClasses,
} from "./ResolutionStatusCell";

afterEach(() => {
  cleanup();
});

// Local-time ISO so the default dd/MM format is timezone-independent.
const RESOLVED_AT = new Date(2026, 10, 13, 9, 5).toISOString();

describe("ResolutionStatusCell — states", () => {
  it("emits dual-class names, data attributes and the variant modifier", () => {
    const cn = resolutionStatusCellBemClasses("itp");
    expect(cn.root).toBe("itp-resolution-status-cell delpi-ui-resolution-status-cell");
    const { container } = render(
      <ResolutionStatusCell prefix="itp" status="open" onResolve={() => undefined} />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("delpi-ui-resolution-status-cell--cell");
    expect(root.className).toContain("itp-resolution-status-cell--cell");
    expect(root.getAttribute("data-status")).toBe("open");
  });

  it("open: shows a 'Resolver' button that calls onResolve", () => {
    const onResolve = vi.fn();
    render(<ResolutionStatusCell status="open" onResolve={onResolve} />);
    fireEvent.click(screen.getByRole("button", { name: "Resolver" }));
    expect(onResolve).toHaveBeenCalledOnce();
  });

  it("open without onResolve renders no control", () => {
    render(<ResolutionStatusCell status="open" />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("resolved: '✓ dd/MM' with tooltip (who/when) and a 'Reabrir' button", () => {
    const onReopen = vi.fn();
    const { container } = render(
      <ResolutionStatusCell
        status="resolved"
        resolvedAt={RESOLVED_AT}
        resolvedBy="Maria"
        onReopen={onReopen}
      />,
    );
    const status = container.querySelector<HTMLElement>(".delpi-ui-resolution-status-cell__status")!;
    expect(status.textContent).toContain("13/11");
    expect(status.textContent).toContain("✓");
    expect(status.getAttribute("title")).toBe("Resolvida em 13/11 por Maria");
    expect(status.textContent).toContain("Resolvida"); // sr-only text for assistive tech
    fireEvent.click(screen.getByRole("button", { name: "Reabrir" }));
    expect(onReopen).toHaveBeenCalledOnce();
  });

  it("resolved without user falls back to the resolved label + date (no dangling placeholder)", () => {
    const { container } = render(
      <ResolutionStatusCell status="resolved" resolvedAt={RESOLVED_AT} />,
    );
    const title = container
      .querySelector(".delpi-ui-resolution-status-cell__status")!
      .getAttribute("title")!;
    expect(title).toBe("Resolvida — 13/11");
    expect(title).not.toContain("{");
  });

  it("not_applicable: 'Explicada' text and no button even with handlers", () => {
    render(
      <ResolutionStatusCell
        status="not_applicable"
        onResolve={() => undefined}
        onReopen={() => undefined}
      />,
    );
    expect(screen.getByText("Explicada")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("labels are overridable", () => {
    render(
      <ResolutionStatusCell
        status="open"
        onResolve={() => undefined}
        labels={{ resolve: "Concluir" }}
      />,
    );
    expect(screen.getByRole("button", { name: "Concluir" })).toBeTruthy();
  });

  it("dateFormatter overrides the default for status and detail", () => {
    const { container } = render(
      <ResolutionStatusCell
        status="resolved"
        resolvedAt={RESOLVED_AT}
        resolvedBy="Maria"
        dateFormatter={() => "ONTEM"}
        variant="full"
        onReopen={() => undefined}
      />,
    );
    expect(container.querySelector(".delpi-ui-resolution-status-cell__detail")?.textContent).toBe(
      "Resolvida em ONTEM por Maria",
    );
  });

  it("default date formats: dd/MM and dd/MM/yyyy HH:mm; invalid input yields empty", () => {
    expect(formatResolutionDate(RESOLVED_AT, false)).toBe("13/11");
    expect(formatResolutionDate(RESOLVED_AT, true)).toBe("13/11/2026 09:05");
    expect(formatResolutionDate("not a date", false)).toBe("");
  });
});

describe("ResolutionStatusCell — variants", () => {
  it("compact keeps the cell content structure", () => {
    const { container } = render(
      <ResolutionStatusCell
        variant="compact"
        status="resolved"
        resolvedAt={RESOLVED_AT}
        onReopen={() => undefined}
      />,
    );
    expect(container.firstElementChild?.className).toContain("delpi-ui-resolution-status-cell--compact");
    expect(container.textContent).toContain("13/11");
    expect(container.querySelector(".delpi-ui-resolution-status-cell__detail")).toBeNull();
  });

  it("full open: wide primary 'Marcar como resolvida'", () => {
    const onResolve = vi.fn();
    render(<ResolutionStatusCell variant="full" status="open" onResolve={onResolve} />);
    const button = screen.getByRole("button", { name: "Marcar como resolvida" });
    expect(button.className).toContain("delpi-ui-action-btn--primary");
    fireEvent.click(button);
    expect(onResolve).toHaveBeenCalledOnce();
  });

  it("full resolved: visible 'Resolvida em … por …' line and a secondary 'Reabrir'", () => {
    const { container } = render(
      <ResolutionStatusCell
        variant="full"
        status="resolved"
        resolvedAt={RESOLVED_AT}
        resolvedBy="Maria"
        onReopen={() => undefined}
      />,
    );
    expect(container.querySelector(".delpi-ui-resolution-status-cell__detail")?.textContent).toBe(
      "Resolvida em 13/11/2026 09:05 por Maria",
    );
    const reopen = screen.getByRole("button", { name: "Reabrir" });
    expect(reopen.className).not.toContain("delpi-ui-action-btn--primary");
  });
});

describe("ResolutionStatusCell — async behavior", () => {
  it("shows 'Salvando…' until a resolving promise settles, then restores", async () => {
    let finish!: () => void;
    const onResolve = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
    render(<ResolutionStatusCell status="open" onResolve={onResolve} />);
    fireEvent.click(screen.getByRole("button", { name: "Resolver" }));
    const busy = screen.getByRole("button", { name: "Salvando…" });
    expect((busy as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(busy);
    expect(onResolve).toHaveBeenCalledTimes(1);
    await act(async () => {
      finish();
    });
    await waitFor(() => expect(screen.getByRole("button", { name: "Resolver" })).toBeTruthy());
  });

  it("rejection returns to the previous state without throwing", async () => {
    const onResolve = vi.fn(() => Promise.reject(new Error("falhou")));
    render(<ResolutionStatusCell status="open" onResolve={onResolve} />);
    fireEvent.click(screen.getByRole("button", { name: "Resolver" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Resolver" })).toBeTruthy());
    expect(onResolve).toHaveBeenCalledOnce();
  });

  it("synchronous throw leaves the cell usable", () => {
    const onResolve = vi.fn(() => {
      throw new Error("sync");
    });
    render(<ResolutionStatusCell status="open" onResolve={onResolve} />);
    fireEvent.click(screen.getByRole("button", { name: "Resolver" }));
    expect(screen.getByRole("button", { name: "Resolver" })).toBeTruthy();
  });

  it("promise success transitions through the consumer-owned status (open → resolved)", async () => {
    function Harness() {
      const [status, setStatus] = useState<"open" | "resolved">("open");
      return (
        <ResolutionStatusCell
          status={status}
          resolvedAt={status === "resolved" ? RESOLVED_AT : null}
          onResolve={async () => {
            await Promise.resolve();
            setStatus("resolved");
          }}
          onReopen={async () => {
            await Promise.resolve();
            setStatus("open");
          }}
        />
      );
    }
    render(<Harness />);
    fireEvent.click(screen.getByRole("button", { name: "Resolver" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Reabrir" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Reabrir" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Resolver" })).toBeTruthy());
  });

  it("pending (consumer-controlled) shows 'Salvando…' and blocks the action", () => {
    const onResolve = vi.fn();
    const { container } = render(<ResolutionStatusCell status="open" pending onResolve={onResolve} />);
    const button = screen.getByRole("button", { name: "Salvando…" }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    expect(container.firstElementChild?.getAttribute("aria-busy")).toBe("true");
    fireEvent.click(button);
    expect(onResolve).not.toHaveBeenCalled();
  });

  it("disabled blocks the action", () => {
    const onResolve = vi.fn();
    render(<ResolutionStatusCell status="open" disabled onResolve={onResolve} />);
    const button = screen.getByRole("button", { name: "Resolver" }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(onResolve).not.toHaveBeenCalled();
  });
});

describe("ResolutionStatusCell — accessibility and row isolation", () => {
  it("contextLabel names the actions: 'Resolver NF 25655' / 'Reabrir NF 25655'", () => {
    const { rerender } = render(
      <ResolutionStatusCell status="open" contextLabel="NF 25655" onResolve={() => undefined} />,
    );
    expect(screen.getByRole("button", { name: "Resolver NF 25655" })).toBeTruthy();
    rerender(
      <ResolutionStatusCell
        status="resolved"
        resolvedAt={RESOLVED_AT}
        contextLabel="NF 25655"
        onReopen={() => undefined}
      />,
    );
    expect(screen.getByRole("button", { name: "Reabrir NF 25655" })).toBeTruthy();
  });

  it("full variant context names the primary action", () => {
    render(
      <ResolutionStatusCell
        variant="full"
        status="open"
        contextLabel="NF 1"
        onResolve={() => undefined}
      />,
    );
    expect(screen.getByRole("button", { name: "Marcar como resolvida NF 1" })).toBeTruthy();
  });

  it("without contextLabel the visible text is the accessible name", () => {
    render(<ResolutionStatusCell status="open" onResolve={() => undefined} />);
    expect(screen.getByRole("button", { name: "Resolver" }).hasAttribute("aria-label")).toBe(false);
  });

  it("click and Enter/Space do not bubble to an ancestor row handler", () => {
    const onRow = vi.fn();
    const onRowKey = vi.fn();
    render(
      <div onClick={onRow} onKeyDown={onRowKey}>
        <ResolutionStatusCell status="open" onResolve={() => undefined} />
      </div>,
    );
    const button = screen.getByRole("button", { name: "Resolver" });
    fireEvent.click(button);
    fireEvent.keyDown(button, { key: "Enter" });
    fireEvent.keyDown(button, { key: " " });
    expect(onRow).not.toHaveBeenCalled();
    expect(onRowKey).not.toHaveBeenCalled();
  });

  it("negative: other keys (Tab/Escape) still bubble for table keyboard navigation", () => {
    const onRowKey = vi.fn();
    render(
      <div onKeyDown={onRowKey}>
        <ResolutionStatusCell status="open" onResolve={() => undefined} />
      </div>,
    );
    fireEvent.keyDown(screen.getByRole("button", { name: "Resolver" }), { key: "Tab" });
    expect(onRowKey).toHaveBeenCalledOnce();
  });

  it("inside a DataTable row: resolving does not trigger onRowClick (interactive column)", () => {
    type Row = { id: string };
    const onRowClick = vi.fn();
    const onResolve = vi.fn();
    render(
      <DataTable<Row>
        columns={[
          { key: "id", header: "Id", render: (row) => row.id },
          {
            key: "resolution",
            header: "Tratada",
            interactive: true,
            render: () => <ResolutionStatusCell status="open" onResolve={onResolve} />,
          },
        ]}
        rows={[{ id: "1" }]}
        rowKey={(row) => row.id}
        classNames={dataTableBemClasses("itp")}
        labels={{
          emptyMessage: "Vazio",
          loadingMessage: "Carregando",
          sortByAriaLabel: (header: string) => `Ordenar ${header}`,
          headerHelpAriaLabel: (header: string) => `Ajuda ${header}`,
        }}
        onRowClick={onRowClick}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Resolver" }));
    expect(onResolve).toHaveBeenCalledOnce();
    expect(onRowClick).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("1"));
    expect(onRowClick).toHaveBeenCalledOnce();
  });

  it("factory binds the prefix", () => {
    const Cell = createDashboardResolutionStatusCell({ prefix: "fx" });
    const { container } = render(<Cell status="open" onResolve={() => undefined} />);
    expect(container.querySelector(".fx-resolution-status-cell.delpi-ui-resolution-status-cell")).toBeTruthy();
  });

  it("dark theme: no inline colors (tokens only)", () => {
    document.documentElement.setAttribute("data-theme", "dark");
    const { container } = render(
      <ResolutionStatusCell status="resolved" resolvedAt={RESOLVED_AT} onReopen={() => undefined} />,
    );
    expect(container.querySelector("[style]")).toBeNull();
    document.documentElement.removeAttribute("data-theme");
  });
});

describe("ResolutionStatusCell — styles contract", () => {
  it("styles.css imports the stylesheet", async () => {
    const { readFileSync } = await import("node:fs");
    const { resolve } = await import("node:path");
    const entry = readFileSync(resolve(__dirname, "../../styles.css"), "utf8");
    expect(entry).toContain('@import "./styles/resolution-status-cell.css"');
  });
});
