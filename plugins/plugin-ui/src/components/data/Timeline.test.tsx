import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  createTimeline,
  timelineBemClasses,
  timelineMarkerToneClass,
} from "./Timeline";

afterEach(() => {
  cleanup();
});

describe("Timeline", () => {
  it("timelineBemClasses emite dual-class", () => {
    const cn = timelineBemClasses("dm");
    expect(cn.track).toContain("dm-timeline__track");
    expect(cn.track).toContain("delpi-ui-timeline__track");
  });

  it("timelineMarkerToneClass omite default e dual-class nos tons", () => {
    expect(timelineMarkerToneClass("dm", "default")).toBe("");
    expect(timelineMarkerToneClass("dm", "danger")).toBe(
      "dm-timeline__marker--danger delpi-ui-timeline__marker--danger",
    );
  });

  it("renderiza itens com título, detalhe e meta", () => {
    const TimelineView = createTimeline({ prefix: "dm" });
    render(
      <TimelineView
        items={[
          {
            id: "1",
            title: "Reposição registrada",
            timeLabel: "15/07/2026, 14:45",
            occurredAt: "2026-07-15T14:45:00",
            detail: "Peça 3019 · 10 golpes",
            meta: "Usuário: Ana",
            tone: "success",
          },
        ]}
      />,
    );

    expect(screen.getByText("Reposição registrada")).toBeTruthy();
    expect(screen.getByText("Peça 3019 · 10 golpes")).toBeTruthy();
    expect(screen.getByText("Usuário: Ana")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-timeline__marker--success")).toBeTruthy();
  });

  it("variante table renderiza cabeçalhos e células alinhadas", () => {
    const TimelineView = createTimeline({ prefix: "dm" });
    render(
      <TimelineView
        variant="table"
        columnLabels={{ time: "Quando", title: "Ação", detail: "Detalhe", meta: "Usuário" }}
        items={[
          {
            id: "1",
            title: "Reposição registrada",
            timeLabel: "15/07/2026, 14:45",
            detail: "Peça 3019",
            meta: "Ana",
            tone: "success",
          },
        ]}
      />,
    );

    expect(document.querySelector(".delpi-ui-timeline--table")).toBeTruthy();
    expect(screen.getByRole("columnheader", { name: "Quando" })).toBeTruthy();
    expect(screen.getByRole("columnheader", { name: "Ação" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Ana" })).toBeTruthy();
  });

  it("mostra empty quando sem itens", () => {
    const TimelineView = createTimeline({ prefix: "dm" });
    render(<TimelineView items={[]} emptyMessage="Sem eventos." />);
    expect(screen.getByText("Sem eventos.")).toBeTruthy();
  });
});
