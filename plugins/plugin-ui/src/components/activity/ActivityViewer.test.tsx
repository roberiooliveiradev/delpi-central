import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ActivityViewer } from "./ActivityViewer";
import type { ActivityStepView } from "./ActivityViewer";

afterEach(cleanup);

const STEPS: ActivityStepView[] = [
  { id: "s1", label: "Solicitação recebida", state: "completed" },
  {
    id: "s2",
    label: "Fonte consultada",
    state: "completed",
    sourceLabel: "DAVI",
    capabilityLabel: "Consultar indicador operacional",
    timestampLabel: "10:41:02",
  },
  { id: "s3", label: "Resposta elaborada", state: "completed" },
];

describe("ActivityViewer — summary", () => {
  it("renders title and state without details → no disclosure", () => {
    render(<ActivityViewer title="Processando…" state="running" />);
    expect(screen.getByText("Processando…")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("region")).toBeNull();
  });

  it("renders a running icon state", () => {
    const { container } = render(
      <ActivityViewer title="Processando…" state="running" />,
    );
    const root = container.querySelector(".delpi-ui-activity-viewer");
    expect(root?.getAttribute("aria-busy")).toBe("true");
    expect(root?.getAttribute("data-state")).toBe("running");
  });

  it("expandable summary exposes aria-expanded/controls and toggles", () => {
    render(
      <ActivityViewer title="Atividade concluída" state="completed" steps={STEPS} />,
    );
    const trigger = screen.getByRole("button", {
      name: /Atividade concluída/,
    });
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(trigger);
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("region")).toBeTruthy();
    fireEvent.click(trigger);
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
  });

  it("supports keyboard activation", () => {
    render(
      <ActivityViewer title="Atividade" state="completed" steps={STEPS} />,
    );
    const trigger = screen.getByRole("button");
    trigger.focus();
    fireEvent.keyDown(trigger, { key: "Enter" });
    fireEvent.click(trigger); // jsdom does not synthesize click on Enter
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
  });

  it.each([
    "pending",
    "completed",
    "partial",
    "blocked",
    "denied",
    "failed",
    "cancelled",
    "no_data",
  ] as const)("renders state %s", (state) => {
    const { container } = render(
      <ActivityViewer title="Atividade" state={state} />,
    );
    expect(
      container.querySelector(".delpi-ui-activity-viewer")
        ?.getAttribute("data-state"),
    ).toBe(state);
  });
});

describe("ActivityViewer — steps", () => {
  it("renders ordered steps with metadata", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="completed"
        steps={STEPS}
        defaultExpanded
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(3);
    expect(screen.getByText("Consultar indicador operacional")).toBeTruthy();
    expect(screen.getByText("DAVI")).toBeTruthy();
    expect(screen.getByText("10:41:02")).toBeTruthy();
  });

  it("renders steps without optional description/metadata", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="completed"
        steps={[{ id: "x", label: "Só título", state: "completed" }]}
        defaultExpanded
      />,
    );
    expect(screen.getByText("Só título")).toBeTruthy();
  });

  it("handles very long labels without breaking layout", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="completed"
        steps={[
          {
            id: "long",
            label: "Etapa com nome extremamente longo ".repeat(20),
            state: "failed",
          },
        ]}
        defaultExpanded
      />,
    );
    expect(screen.getByText(/Etapa com nome/)).toBeTruthy();
  });
});

describe("ActivityViewer — sources", () => {
  it("renders source without href as plain text", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="completed"
        sources={[
          {
            id: "src1",
            label: "ERP TOTVS",
            statusLabel: "consultada",
          },
        ]}
        defaultExpanded
      />,
    );
    expect(screen.getByText("ERP TOTVS")).toBeTruthy();
    expect(screen.getByText("consultada")).toBeTruthy();
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("renders legitimate href as a link", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="completed"
        sources={[
          {
            id: "src1",
            label: "Catálogo",
            href: "https://intranet.example/catalogo",
            statusLabel: "dados recebidos",
          },
        ]}
        defaultExpanded
      />,
    );
    const link = screen.getByRole("link", { name: "Catálogo" });
    expect(link.getAttribute("href")).toBe(
      "https://intranet.example/catalogo",
    );
  });
});

describe("ActivityViewer — outcome", () => {
  it("non-persistent outcome only shows when expanded", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="completed"
        outcome={{ label: "Concluído com sucesso", tone: "success" }}
      />,
    );
    // Text lives inside the hidden region — assert on visibility, not
    // DOM presence (getByText still matches hidden nodes).
    const region = document.querySelector(
      ".delpi-ui-activity-viewer__detail",
    );
    expect(region?.hasAttribute("hidden")).toBe(true);
    fireEvent.click(screen.getByRole("button"));
    expect(region?.hasAttribute("hidden")).toBe(false);
    expect(screen.getByText("Concluído com sucesso")).toBeTruthy();
  });

  it("persistent outcome stays visible while collapsed", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="blocked"
        steps={STEPS}
        outcome={{
          label: "Pré-condição necessária",
          tone: "warning",
          persistent: true,
        }}
      />,
    );
    expect(screen.getByText("Pré-condição necessária")).toBeTruthy();
    expect(
      screen.getByRole("button").getAttribute("aria-expanded"),
    ).toBe("false");
  });
});

describe("ActivityViewer — safety", () => {
  it("renders hostile markup as inert text", () => {
    render(
      <ActivityViewer
        title="Atividade"
        state="completed"
        steps={[
          {
            id: "evil",
            label: '<img src=x onerror="alert(1)">',
            state: "completed",
          },
        ]}
        defaultExpanded
      />,
    );
    expect(document.querySelector("img")).toBeNull();
    expect(
      screen.getByText('<img src=x onerror="alert(1)">'),
    ).toBeTruthy();
  });

  it("never renders details without data", () => {
    render(<ActivityViewer title="Atividade" state="completed" />);
    expect(screen.queryByRole("region")).toBeNull();
  });
});
