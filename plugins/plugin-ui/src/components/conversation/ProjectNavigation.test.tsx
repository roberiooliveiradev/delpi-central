import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProjectNavigation } from "./ProjectNavigation";

afterEach(cleanup);

describe("ProjectNavigation", () => {
  it("renders unavailable by default with no invented project, search or creation", () => {
    render(<ProjectNavigation />);
    expect(screen.getByText(/após a integração autorizada/)).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("renders authorized project rows and selection only with an explicit callback", () => {
    const onSelectProject = vi.fn();
    render(<ProjectNavigation status="ready" projects={[{ id: "known", title: "Projeto autorizado", selected: true }]} onSelectProject={onSelectProject} />);
    const row = screen.getByRole("button", { name: "Projeto autorizado" });
    expect(row.getAttribute("aria-current")).toBe("page");
    fireEvent.click(row);
    expect(onSelectProject).toHaveBeenCalledTimes(1);
    expect(onSelectProject).toHaveBeenCalledWith("known");
    expect(screen.queryByRole("button", { name: /novo projeto/i })).toBeNull();
  });

  it("does not expose a list when selection is not contracted", () => {
    render(<ProjectNavigation status="ready" projects={[{ id: "hidden", title: "Sem integração" }]} />);
    expect(screen.queryByText("Sem integração")).toBeNull();
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("distinguishes loading, authoritative empty and error with optional retry", () => {
    const onRetry = vi.fn();
    const { rerender } = render(<ProjectNavigation status="loading" />);
    expect(screen.getByRole("status")).toBeTruthy();
    rerender(<ProjectNavigation status="authorized_empty" />);
    expect(screen.getByText("Nenhum projeto disponível.")).toBeTruthy();
    rerender(<ProjectNavigation status="error" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders untrusted-looking project titles as plain text", () => {
    const title = "<img src=x onerror=alert(1)>";
    const { container } = render(<ProjectNavigation status="ready" projects={[{ id: "1", title }]} onSelectProject={vi.fn()} />);
    expect(screen.getByRole("button", { name: title }).textContent).toBe(title);
    expect(container.querySelector("img")).toBeNull();
  });
});
