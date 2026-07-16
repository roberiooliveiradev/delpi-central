import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  buildTimelineForest,
  createTimeline,
  timelineBemClasses,
  timelineMarkerToneClass,
} from "./Timeline";

afterEach(() => {
  cleanup();
});

describe("Timeline", () => {
  it("timelineBemClasses emite dual-class incluindo tree", () => {
    const cn = timelineBemClasses("dm");
    expect(cn.track).toContain("dm-timeline__track");
    expect(cn.track).toContain("delpi-ui-timeline__track");
    expect(cn.rootTree).toContain("delpi-ui-timeline--tree");
    expect(cn.trackNested).toContain("delpi-ui-timeline__track--nested");
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

  it("mostra empty quando sem itens", () => {
    const TimelineView = createTimeline({ prefix: "dm" });
    render(<TimelineView items={[]} emptyMessage="Sem eventos." />);
    expect(screen.getByText("Sem eventos.")).toBeTruthy();
  });

  it("buildTimelineForest monta raiz e branches por parentId", () => {
    const forest = buildTimelineForest([
      { id: "v1", title: "v1" },
      { id: "v2", title: "v2", parentId: "v1" },
      { id: "v2a", title: "v2a", parentId: "v2", branchKey: "alt-a" },
      { id: "v3", title: "v3", parentId: "v2" },
    ]);

    expect(forest).toHaveLength(1);
    expect(forest[0].item.id).toBe("v1");
    expect(forest[0].children).toHaveLength(1);
    expect(forest[0].children[0].item.id).toBe("v2");
    expect(forest[0].children[0].children.map((n) => n.item.id)).toEqual(["v2a", "v3"]);
  });

  it("buildTimelineForest trata pai inexistente e ciclo como raiz", () => {
    const orphanForest = buildTimelineForest([
      { id: "a", title: "a", parentId: "missing" },
      { id: "b", title: "b", parentId: "a" },
    ]);
    expect(orphanForest[0].item.id).toBe("a");
    expect(orphanForest[0].children[0].item.id).toBe("b");

    const cycleForest = buildTimelineForest([
      { id: "x", title: "x", parentId: "y" },
      { id: "y", title: "y", parentId: "x" },
    ]);
    expect(cycleForest.length).toBeGreaterThanOrEqual(1);
    const ids = cycleForest.flatMap(function walk(n): string[] {
      return [n.item.id, ...n.children.flatMap(walk)];
    });
    expect(new Set(ids).size).toBe(2);
  });

  it("layout tree aninha branches e marca data-branch-key", () => {
    const TimelineView = createTimeline({ prefix: "dm" });
    render(
      <TimelineView
        layout="tree"
        items={[
          { id: "v1", title: "Baseline" },
          { id: "v2", title: "Implantação", parentId: "v1" },
          {
            id: "v2a",
            title: "Correção paralela",
            parentId: "v2",
            branchKey: "alt-a",
          },
        ]}
      />,
    );

    expect(document.querySelector(".delpi-ui-timeline--tree")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-timeline__track--nested")).toBeTruthy();
    expect(document.querySelector('[data-branch-key="alt-a"]')).toBeTruthy();
    expect(screen.getByText("Correção paralela")).toBeTruthy();
  });
});
