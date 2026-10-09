// @vitest-environment jsdom
/**
 * G9-LAYOUT-1 — container-fit hierárquico: leaves cresceram (text-fit)
 * mas lanes/pools/subprocess não acompanhavam → filhos vazavam dos
 * containers. Aqui: fit bottom-up a partir do bounding box REAL dos
 * filhos + padding governado, lanes irmãs normalizadas, participant
 * englobando a stack, edges revalidadas (shift-preserving / reroute).
 */
import { describe, expect, it } from "vitest";

import type { ElkNode } from "./elkGraph";
import type { LayoutSnapshot } from "./elkGraph";
import { LAYOUT_PROFILE_V1, containerPadFor } from "./layoutProfile";
import { buildDiOps, type DiLayoutOp } from "./diProposal";

type Bounds = { x: number; y: number; width: number; height: number };

const EPS = 0.01;

function boundsOf(ops: DiLayoutOp[], id: string): Bounds {
  const op = ops.find((o) => o.elementId === id);
  expect(op?.bounds, `bounds de ${id}`).toBeTruthy();
  return op!.bounds!;
}

/** child deve estar totalmente dentro do content rect do container
 *  (padding governado já descontado — §45 assertContained). */
function assertContained(
  child: Bounds,
  container: Bounds,
  pad: { left: number; top: number; right: number; bottom: number },
) {
  expect(child.x).toBeGreaterThanOrEqual(container.x + pad.left - EPS);
  expect(child.y).toBeGreaterThanOrEqual(container.y + pad.top - EPS);
  expect(child.x + child.width).toBeLessThanOrEqual(
    container.x + container.width - pad.right + EPS,
  );
  expect(child.y + child.height).toBeLessThanOrEqual(
    container.y + container.height - pad.bottom + EPS,
  );
}

const lanePad = () => containerPadFor("lane");
const poolPad = () => containerPadFor("participant");
const subPad = () => containerPadFor("subprocess");

/** Participant com 1 lane e tasks que transbordam o tamanho ELK da lane
 *  (lane devolvida pequena demais — o defeito do print). */
function overflowingLaneFixture(): {
  snapshot: LayoutSnapshot;
  laidOut: ElkNode;
} {
  const snapshot: LayoutSnapshot = {
    nodes: [
      { id: "POOL", type: "bpmn:participant", isParticipant: true },
      { id: "L1", type: "bpmn:lane", isLane: true, parentId: "POOL" },
      {
        id: "T1",
        type: "bpmn:task",
        parentId: "L1",
        label: "Dados são tratados e indicadores calculados automaticamente",
        width: 280,
        height: 98,
      },
      { id: "T2", type: "bpmn:task", parentId: "L1", width: 140, height: 80 },
      { id: "S1", type: "bpmn:startEvent", parentId: "L1", width: 36, height: 36 },
    ],
    edges: [
      { id: "F1", sourceId: "S1", targetId: "T1" },
      { id: "F2", sourceId: "T1", targetId: "T2" },
    ],
  };
  // ELK posiciona filhos; container veio "antigo" (135 de altura,
  // largura insuficiente p/ T1 280px + T2 + padding).
  const laidOut: ElkNode = {
    id: "__root__",
    children: [
      {
        id: "POOL",
        x: 0,
        y: 0,
        width: 600,
        height: 250,
        children: [
          {
            id: "L1",
            x: 48,
            y: 16,
            width: 400,
            height: 135,
            children: [
              { id: "S1", x: 60, y: 45, width: 36, height: 36 },
              { id: "T1", x: 140, y: 20, width: 280, height: 98 },
              { id: "T2", x: 480, y: 28, width: 140, height: 80 },
            ],
            edges: [
              {
                id: "F1",
                sources: ["S1"],
                targets: ["T1"],
                sections: [
                  {
                    startPoint: { x: 96, y: 63 },
                    endPoint: { x: 140, y: 63 },
                  },
                ],
              } as never,
              {
                id: "F2",
                sources: ["T1"],
                targets: ["T2"],
                sections: [
                  {
                    startPoint: { x: 420, y: 63 },
                    endPoint: { x: 480, y: 63 },
                  },
                ],
              } as never,
            ],
          },
        ],
      },
    ],
  };
  return { snapshot, laidOut };
}

describe("container-fit — lane cresce a partir dos filhos (§14/§18)", () => {
  it("task que transborda força lane a cobrir bounds + padding", () => {
    const { snapshot, laidOut } = overflowingLaneFixture();
    const ops = buildDiOps(laidOut, snapshot);
    const t1 = boundsOf(ops, "T1");
    const t2 = boundsOf(ops, "T2");
    const s1 = boundsOf(ops, "S1");
    const lane = boundsOf(ops, "L1");
    const pad = lanePad();
    for (const child of [t1, t2, s1]) {
      assertContained(child, lane, pad);
    }
    // lane.width cobre o filho mais à direita + right padding
    expect(lane.width).toBeGreaterThanOrEqual(
      t2.x + t2.width + pad.right - lane.x - EPS,
    );
    // lane reserva header à esquerda — nenhum filho invade
    for (const child of [t1, t2, s1]) {
      expect(child.x).toBeGreaterThanOrEqual(lane.x + pad.left - EPS);
    }
  });

  it("participant cresce a partir da lane (§19/§20) — zero overflow", () => {
    const { snapshot, laidOut } = overflowingLaneFixture();
    const ops = buildDiOps(laidOut, snapshot);
    const lane = boundsOf(ops, "L1");
    const pool = boundsOf(ops, "POOL");
    assertContained(lane, pool, poolPad());
  });

  it("edges intra-lane transladam com a lane (shift-preserving)", () => {
    const { snapshot, laidOut } = overflowingLaneFixture();
    const ops = buildDiOps(laidOut, snapshot);
    const f1 = ops.find((o) => o.elementId === "F1");
    const f2 = ops.find((o) => o.elementId === "F2");
    const s1 = boundsOf(ops, "S1");
    const t1 = boundsOf(ops, "T1");
    const t2 = boundsOf(ops, "T2");
    expect(f1?.waypoints?.length).toBeGreaterThanOrEqual(2);
    // endpoints ancoram nos bounds finais: F1 toca S1→T1, F2 toca T1→T2
    const f1w = f1!.waypoints!;
    expect(f1w[0].x).toBeCloseTo(s1.x + s1.width, 0);
    expect(f1w[f1w.length - 1].x).toBeCloseTo(t1.x, 0);
    const f2w = f2!.waypoints!;
    expect(f2w[0].x).toBeCloseTo(t1.x + t1.width, 0);
    expect(f2w[f2w.length - 1].x).toBeCloseTo(t2.x, 0);
  });
});

describe("container-fit — lanes irmãs (§17) e participant (§19/§20)", () => {
  function twoLaneFixture() {
    const snapshot: LayoutSnapshot = {
      nodes: [
        { id: "POOL", type: "bpmn:participant", isParticipant: true },
        { id: "LA", type: "bpmn:lane", isLane: true, parentId: "POOL" },
        { id: "LB", type: "bpmn:lane", isLane: true, parentId: "POOL" },
        { id: "TA", type: "bpmn:task", parentId: "LA", width: 140, height: 80 },
        {
          id: "TB",
          type: "bpmn:task",
          parentId: "LB",
          width: 290,
          height: 98,
        },
      ],
      edges: [{ id: "FX", sourceId: "TA", targetId: "TB" }],
    };
    const laidOut: ElkNode = {
      id: "__root__",
      children: [
        {
          id: "POOL",
          x: 10,
          y: 10,
          width: 500,
          height: 300,
          children: [
            {
              id: "LA",
              x: 48,
              y: 16,
              width: 400,
              height: 130,
              children: [{ id: "TA", x: 60, y: 30, width: 140, height: 80 }],
            },
            {
              id: "LB",
              x: 48,
              y: 150,
              width: 380,
              height: 130,
              children: [{ id: "TB", x: 55, y: 15, width: 290, height: 98 }],
            },
          ],
          edges: [
            {
              id: "FX",
              sources: ["TA"],
              targets: ["TB"],
              sections: [
                {
                  startPoint: { x: 108, y: 110 },
                  bendPoints: [{ x: 108, y: 170 }],
                  endPoint: { x: 103, y: 165 },
                },
              ],
            } as never,
          ],
        },
      ],
    };
    return { snapshot, laidOut };
  }

  it("todas as lanes dividem a mesma largura interna do participant", () => {
    const { snapshot, laidOut } = twoLaneFixture();
    const ops = buildDiOps(laidOut, snapshot);
    const la = boundsOf(ops, "LA");
    const lb = boundsOf(ops, "LB");
    const pool = boundsOf(ops, "POOL");
    expect(la.x).toBeCloseTo(lb.x, 6);
    expect(la.width).toBeCloseTo(lb.width, 6);
    expect(la.width).toBeCloseTo(
      pool.width - poolPad().left - poolPad().right,
      6,
    );
    // lanes empilham flush na ordem do documento
    expect(lb.y).toBeCloseTo(la.y + la.height, 6);
    // filhos contidos em ambas
    assertContained(boundsOf(ops, "TA"), la, lanePad());
    assertContained(boundsOf(ops, "TB"), lb, lanePad());
    assertContained(la, pool, poolPad());
    assertContained(lb, pool, poolPad());
  });

  it("edge cross-lane recebe rota orthogonal entre bounds finais", () => {
    const { snapshot, laidOut } = twoLaneFixture();
    const ops = buildDiOps(laidOut, snapshot);
    const fx = ops.find((o) => o.elementId === "FX");
    const ta = boundsOf(ops, "TA");
    const tb = boundsOf(ops, "TB");
    const w = fx!.waypoints!;
    expect(w.length).toBeGreaterThanOrEqual(2);
    // rota sai/entra pelas bordas reais dos bounds finais
    const first = w[0];
    const last = w[w.length - 1];
    const onBorder = (p: { x: number; y: number }, b: Bounds) =>
      Math.abs(p.x - b.x) < EPS ||
      Math.abs(p.x - (b.x + b.width)) < EPS ||
      Math.abs(p.y - b.y) < EPS ||
      Math.abs(p.y - (b.y + b.height)) < EPS;
    expect(onBorder(first, ta)).toBe(true);
    expect(onBorder(last, tb)).toBe(true);
    // orthogonal: segmentos todos horizontais ou verticais
    for (let i = 1; i < w.length; i++) {
      const horiz = Math.abs(w[i].y - w[i - 1].y) < EPS;
      const vert = Math.abs(w[i].x - w[i - 1].x) < EPS;
      expect(horiz || vert).toBe(true);
    }
  });
});

describe("container-fit — recursividade (§22) e subprocess (§23)", () => {
  it("lane aninhada: filho cabe → lane interna → lane pai → participant", () => {
    const snapshot: LayoutSnapshot = {
      nodes: [
        { id: "POOL", type: "bpmn:participant", isParticipant: true },
        { id: "L1", type: "bpmn:lane", isLane: true, parentId: "POOL" },
        { id: "NL", type: "bpmn:lane", isLane: true, parentId: "L1" },
        { id: "TN", type: "bpmn:task", parentId: "NL", width: 200, height: 90 },
        { id: "TM", type: "bpmn:task", parentId: "L1", width: 140, height: 80 },
      ],
      edges: [],
    };
    const laidOut: ElkNode = {
      id: "__root__",
      children: [
        {
          id: "POOL",
          x: 0,
          y: 0,
          width: 600,
          height: 250,
          children: [
            {
              id: "L1",
              x: 48,
              y: 16,
              width: 400,
              height: 200,
              children: [
                {
                  id: "NL",
                  x: 60,
                  y: 20,
                  width: 200,
                  height: 100,
                  children: [
                    { id: "TN", x: 55, y: 10, width: 200, height: 90 },
                  ],
                },
                { id: "TM", x: 60, y: 140, width: 140, height: 80 },
              ],
            },
          ],
        },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const tn = boundsOf(ops, "TN");
    const nl = boundsOf(ops, "NL");
    const l1 = boundsOf(ops, "L1");
    const pool = boundsOf(ops, "POOL");
    const tm = boundsOf(ops, "TM");
    assertContained(tn, nl, lanePad());
    assertContained(nl, l1, lanePad());
    assertContained(tm, l1, lanePad());
    assertContained(l1, pool, poolPad());
  });

  it("subprocess expandido cresce a partir dos filhos internos", () => {
    const snapshot: LayoutSnapshot = {
      nodes: [
        {
          id: "SUB",
          type: "bpmn:subProcess",
          isExpanded: true,
          width: 350,
          height: 200,
        },
        { id: "TI", type: "bpmn:task", parentId: "SUB", width: 260, height: 98 },
        { id: "T2", type: "bpmn:task", width: 140, height: 80 },
      ],
      edges: [],
    };
    const laidOut: ElkNode = {
      id: "__root__",
      children: [
        {
          id: "SUB",
          x: 100,
          y: 100,
          width: 350,
          height: 200,
          children: [{ id: "TI", x: 30, y: 30, width: 260, height: 98 }],
        },
        { id: "T2", x: 600, y: 120, width: 140, height: 80 },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const ti = boundsOf(ops, "TI");
    const sub = boundsOf(ops, "SUB");
    assertContained(ti, sub, subPad());
    // subprocess cresceu até cobrir o filho + padding
    expect(sub.width).toBeGreaterThanOrEqual(
      ti.x + ti.width + subPad().right - sub.x - EPS,
    );
  });
});

describe("container-fit — lanes raiz sem participant", () => {
  it("lanes de processo sem collaboration empilham e dividem largura", () => {
    const snapshot: LayoutSnapshot = {
      nodes: [
        { id: "LA", type: "bpmn:lane", isLane: true },
        { id: "LB", type: "bpmn:lane", isLane: true },
        { id: "TA", type: "bpmn:task", parentId: "LA", width: 140, height: 80 },
        { id: "TB", type: "bpmn:task", parentId: "LB", width: 260, height: 90 },
      ],
      edges: [],
    };
    // ELK posicionou as lanes lado a lado (compound siblings) — o fit
    // deve empilhar na raiz exatamente como dentro de um participant.
    const laidOut: ElkNode = {
      id: "__root__",
      children: [
        {
          id: "LA",
          x: 0,
          y: 0,
          width: 400,
          height: 135,
          children: [{ id: "TA", x: 60, y: 30, width: 140, height: 80 }],
        },
        {
          id: "LB",
          x: 700,
          y: 0,
          width: 380,
          height: 135,
          children: [{ id: "TB", x: 55, y: 20, width: 260, height: 90 }],
        },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const la = boundsOf(ops, "LA");
    const lb = boundsOf(ops, "LB");
    expect(la.x).toBeCloseTo(lb.x, 6);
    expect(la.width).toBeCloseTo(lb.width, 6);
    expect(lb.y).toBeCloseTo(la.y + la.height, 6);
    assertContained(boundsOf(ops, "TA"), la, lanePad());
    assertContained(boundsOf(ops, "TB"), lb, lanePad());
  });
});

describe("container-fit — pisos e região unlaned", () => {
  it("lane vazia respeita containerMin (piso, não regra principal)", () => {
    const snapshot: LayoutSnapshot = {
      nodes: [
        { id: "POOL", type: "bpmn:participant", isParticipant: true },
        { id: "L1", type: "bpmn:lane", isLane: true, parentId: "POOL" },
      ],
      edges: [],
    };
    const laidOut: ElkNode = {
      id: "__root__",
      children: [
        {
          id: "POOL",
          x: 0,
          y: 0,
          width: 600,
          height: 250,
          children: [{ id: "L1", x: 48, y: 16, width: 100, height: 60 }],
        },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const lane = boundsOf(ops, "L1");
    expect(lane.width).toBeGreaterThanOrEqual(
      LAYOUT_PROFILE_V1.containerMin.lane.width - EPS,
    );
    expect(lane.height).toBeGreaterThanOrEqual(
      LAYOUT_PROFILE_V1.containerMin.lane.height - EPS,
    );
  });

  it("membro unlaned do participant fica abaixo da stack de lanes, contido", () => {
    const snapshot: LayoutSnapshot = {
      nodes: [
        { id: "POOL", type: "bpmn:participant", isParticipant: true },
        { id: "L1", type: "bpmn:lane", isLane: true, parentId: "POOL" },
        { id: "TL", type: "bpmn:task", parentId: "L1", width: 140, height: 80 },
        // PROCESS_LEVEL_UNLANED: filho direto do participant
        { id: "TU", type: "bpmn:task", parentId: "POOL", width: 140, height: 80 },
      ],
      edges: [],
    };
    const laidOut: ElkNode = {
      id: "__root__",
      children: [
        {
          id: "POOL",
          x: 0,
          y: 0,
          width: 600,
          height: 250,
          children: [
            {
              id: "L1",
              x: 48,
              y: 16,
              width: 400,
              height: 135,
              children: [{ id: "TL", x: 60, y: 25, width: 140, height: 80 }],
            },
            // ELK posicionou o unlaned SOBRE a lane — fit deve descer ele
            { id: "TU", x: 60, y: 30, width: 140, height: 80 },
          ],
        },
      ],
    };
    const ops = buildDiOps(laidOut, snapshot);
    const lane = boundsOf(ops, "L1");
    const tu = boundsOf(ops, "TU");
    const pool = boundsOf(ops, "POOL");
    // abaixo da lane + gap do profile
    expect(tu.y).toBeGreaterThanOrEqual(
      lane.y + lane.height + LAYOUT_PROFILE_V1.unlanedGap - EPS,
    );
    assertContained(tu, pool, poolPad());
    expect(pool.height).toBeGreaterThanOrEqual(
      tu.y + tu.height + poolPad().bottom - pool.y - EPS,
    );
  });
});
