/**
 * DI proposal — aplica geometria ELK ao artefato BPMN produzindo
 * BPMNShape/BPMNEdge/BPMNPlane (P5 §15). Proposta é transient: o usuário
 * aceita (vira commands do editor → dirty) ou cancela (descartada).
 *
 * Snapshot/DI usam DOMParser puro — nunca APIs vendor fora de src/editor.
 */

import type { ElkNode } from "./elkGraph";
import type { LayoutSnapshot } from "./elkGraph";

const BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL";
const BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI";
const DC_NS = "http://www.omg.org/spec/DD/20100524/DC";
const DI_NS = "http://www.omg.org/spec/DD/20100524/DI";

const FLOW_NODES = new Set([
  "task", "userTask", "serviceTask", "scriptTask", "manualTask",
  "businessRuleTask", "sendTask", "receiveTask", "callActivity",
  "subProcess", "transaction", "adHocSubProcess", "eventSubProcess",
  "startEvent", "endEvent", "intermediateCatchEvent",
  "intermediateThrowEvent", "boundaryEvent",
  "exclusiveGateway", "parallelGateway", "inclusiveGateway",
  "eventBasedGateway", "complexGateway",
  "participant", "lane", "dataObject", "dataObjectReference",
  "dataStoreReference", "textAnnotation", "group",
]);

const EDGES = new Set([
  "sequenceFlow", "messageFlow", "association", "dataInputAssociation",
  "dataOutputAssociation", "conversation",
]);

const CONTAINERS = new Set(["process", "subProcess", "transaction", "adHocSubProcess", "laneSet"]);

/** Famílias cujo tamanho o layout PODE recalcular (contêm filhos).
 *  Todo o resto é SIZE_PRESERVED — auto-layout move, não redimensiona. */
const RESIZABLE_CONTAINERS = new Set([
  "subProcess",
  "transaction",
  "adHocSubProcess",
  "eventSubProcess",
  "participant",
  "lane",
]);

function mayResize(node: LayoutSnapshot["nodes"][number]): boolean {
  if (node.isParticipant || node.isLane) return true;
  return RESIZABLE_CONTAINERS.has(node.type.replace(/^bpmn:/, ""));
}

/** Extrai o snapshot de layout de um BPMN XML (sem DI necessário).
 *  Quando há BPMN-DI, captura os bounds atuais por bpmnElement —
 *  a fonte de verdade do tamanho é o DI vigente, não o default vendor. */
export function snapshotFromXml(xml: string): LayoutSnapshot {
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  const nodes: LayoutSnapshot["nodes"] = [];
  const edges: LayoutSnapshot["edges"] = [];

  const readBounds = (el: Element | undefined) => {
    if (!el) return undefined;
    const b = {
      x: Number(el.getAttribute("x")),
      y: Number(el.getAttribute("y")),
      width: Number(el.getAttribute("width")),
      height: Number(el.getAttribute("height")),
    };
    return Object.values(b).every(Number.isFinite) ? b : undefined;
  };
  const readLabel = (diEl: Element) => {
    const label = diEl.getElementsByTagNameNS(BPMNDI_NS, "BPMNLabel")[0];
    return label
      ? readBounds(label.getElementsByTagNameNS(DC_NS, "Bounds")[0])
      : undefined;
  };

  const diSize = new Map<
    string,
    { x: number; y: number; width: number; height: number; label?: DiBounds }
  >();
  for (const shape of Array.from(
    doc.getElementsByTagNameNS(BPMNDI_NS, "BPMNShape"),
  )) {
    const ref = shape.getAttribute("bpmnElement");
    const b = readBounds(
      shape.getElementsByTagNameNS(DC_NS, "Bounds")[0],
    );
    if (ref && b) {
      diSize.set(ref, { ...b, label: readLabel(shape) });
    }
  }
  const diEdge = new Map<
    string,
    { points: { x: number; y: number }[]; label?: DiBounds }
  >();
  for (const edge of Array.from(
    doc.getElementsByTagNameNS(BPMNDI_NS, "BPMNEdge"),
  )) {
    const ref = edge.getAttribute("bpmnElement");
    const points = Array.from(
      edge.getElementsByTagNameNS(DI_NS, "waypoint"),
    ).map((w) => ({
      x: Number(w.getAttribute("x")),
      y: Number(w.getAttribute("y")),
    }));
    if (ref && points.length) {
      diEdge.set(ref, { points, label: readLabel(edge) });
    }
  }

  const localName = (el: Element) => el.localName || el.tagName.split(":").pop() || "";

  const walk = (el: Element, parentId?: string) => {
    for (const child of Array.from(el.children)) {
      const name = localName(child);
      const id = child.getAttribute("id");
      if (!id) continue;
      if (FLOW_NODES.has(name)) {
        const size = diSize.get(id);
        nodes.push({
          id,
          type: `bpmn:${name}`,
          parentId,
          x: size?.x,
          y: size?.y,
          width: size?.width,
          height: size?.height,
          labelBounds: size?.label,
          isBoundary: name === "boundaryEvent",
          attachedToId: child.getAttribute("attachedToRef") ?? undefined,
          isLane: name === "lane",
          isParticipant: name === "participant",
        });
        walk(child, id);
      } else if (EDGES.has(name)) {
        const source = child.getAttribute("sourceRef");
        const target = child.getAttribute("targetRef");
        if (source && target) {
          const di = diEdge.get(id);
          edges.push({
            id,
            sourceId: source,
            targetId: target,
            points: di?.points,
            labelBounds: di?.label,
          });
        }
      } else if (CONTAINERS.has(name) || name === "collaboration" || name === "definitions") {
        walk(child, parentId);
      }
    }
  };
  walk(doc.documentElement);
  return { nodes, edges };
}

export function hasBpmnDi(xml: string): boolean {
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  return doc.getElementsByTagNameNS(BPMNDI_NS, "BPMNDiagram").length > 0;
}

export type DiBounds = { x: number; y: number; width: number; height: number };

/** Operação geométrica por elemento — consumida pelo editor como
 *  UM comando (single logical batch) no Accept do preview (P5 §18). */
export type DiLayoutOp = {
  elementId: string;
  bounds?: DiBounds;
  waypoints?: Array<{ x: number; y: number }>;
  /** Bounds resolvidas da BPMNLabel externa (delta do owner). */
  labelBounds?: DiBounds;
};

type LayoutGeometry = {
  bounds: Map<string, DiBounds>;
  edgePoints: Map<string, Array<{ x: number; y: number }>>;
  /** Labels externas explicitas: novas bounds após o delta do owner. */
  labels: Map<string, DiBounds>;
};

/** Ponto médio de uma polyline (50% do comprimento) — mesmo referencial
 *  que o vendor usa para posicionar labels de connection. */
export function polylineMid(
  points: Array<{ x: number; y: number }>,
): { x: number; y: number } {
  if (!points.length) return { x: 0, y: 0 };
  if (points.length === 1) return points[0];
  let total = 0;
  const segs: number[] = [];
  for (let i = 1; i < points.length; i++) {
    const len = Math.hypot(
      points[i].x - points[i - 1].x,
      points[i].y - points[i - 1].y,
    );
    segs.push(len);
    total += len;
  }
  let rest = total / 2;
  for (let i = 0; i < segs.length; i++) {
    if (rest <= segs[i] || i === segs.length - 1) {
      const t = segs[i] === 0 ? 0 : rest / segs[i];
      return {
        x: points[i].x + (points[i + 1].x - points[i].x) * t,
        y: points[i].y + (points[i + 1].y - points[i].y) * t,
      };
    }
    rest -= segs[i];
  }
  return points[points.length - 1];
}

function computeGeometry(laidOut: ElkNode): LayoutGeometry {
  const bounds = new Map<string, DiBounds>();
  const edgePoints = new Map<string, Array<{ x: number; y: number }>>();

  const collect = (node: ElkNode, ox = 0, oy = 0) => {
    const x = ox + ((node as unknown as { x?: number }).x ?? 0);
    const y = oy + ((node as unknown as { y?: number }).y ?? 0);
    if (node.id !== "__root__") {
      bounds.set(node.id, {
        x,
        y,
        width: node.width ?? 100,
        height: node.height ?? 80,
      });
    }
    for (const edge of (node as unknown as { edges?: Array<{ id: string; sections?: Array<{ startPoint: { x: number; y: number }; endPoint: { x: number; y: number }; bendPoints?: Array<{ x: number; y: number }> }> }> }).edges ?? []) {
      const section = edge.sections?.[0];
      if (section) {
        const pts = [
          { x: x + section.startPoint.x, y: y + section.startPoint.y },
          ...(section.bendPoints ?? []).map((p) => ({ x: x + p.x, y: y + p.y })),
          { x: x + section.endPoint.x, y: y + section.endPoint.y },
        ];
        edgePoints.set(edge.id, pts);
      }
    }
    for (const child of node.children ?? []) collect(child, x, y);
  };
  collect(laidOut);
  return { bounds, edgePoints, labels: new Map() };
}

/** Geometria final: posições ELK + width/height vigentes para nós que
 *  não podem ser redimensionados pelo layout (SIZE_PRESERVED).
 *  Containers (pool/lane/subProcess expandido) mantêm o tamanho ELK. */
function resolveGeometry(
  laidOut: ElkNode,
  snapshot: LayoutSnapshot,
): LayoutGeometry {
  const geometry = computeGeometry(laidOut);
  const byId = new Map(snapshot.nodes.map((n) => [n.id, n]));
  for (const [id, b] of geometry.bounds) {
    const node = byId.get(id);
    if (!node || mayResize(node)) continue;
    if (node.width != null && node.height != null) {
      b.width = node.width;
      b.height = node.height;
    }
  }

  // Labels externas explícitas acompanham o owner pelo mesmo delta,
  // preservando offset custom do usuário e dims da label.
  for (const node of snapshot.nodes) {
    const label = node.labelBounds;
    const nb = geometry.bounds.get(node.id);
    if (!label || !nb || node.x == null || node.y == null) continue;
    geometry.labels.set(node.id, {
      x: label.x + (nb.x - node.x),
      y: label.y + (nb.y - node.y),
      width: label.width,
      height: label.height,
    });
  }
  const edgeById = new Map(snapshot.edges.map((e) => [e.id, e]));
  for (const [id, pts] of geometry.edgePoints) {
    const edge = edgeById.get(id);
    const label = edge?.labelBounds;
    if (!edge?.points?.length || !label) continue;
    const midOld = polylineMid(edge.points);
    const midNew = polylineMid(pts);
    geometry.labels.set(id, {
      x: label.x + (midNew.x - midOld.x),
      y: label.y + (midNew.y - midOld.y),
      width: label.width,
      height: label.height,
    });
  }
  return geometry;
}

/** Ops geométricas por elemento (ordem estável: nodes depois edges). */
export function buildDiOps(
  laidOut: ElkNode,
  snapshot: LayoutSnapshot,
): DiLayoutOp[] {
  const { bounds, edgePoints, labels } = resolveGeometry(
    laidOut,
    snapshot,
  );
  const ops: DiLayoutOp[] = [];
  for (const [elementId, b] of bounds)
    ops.push({ elementId, bounds: b, labelBounds: labels.get(elementId) });
  for (const [elementId, pts] of edgePoints)
    ops.push({
      elementId,
      waypoints: pts,
      labelBounds: labels.get(elementId),
    });
  return ops;
}

/** Remove todos os BPMNDiagram do XML — usado para montar o artefato
 *  transient de preview (nunca o artefato canônico persistido). */
export function stripBpmnDi(xml: string): string {
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  for (const d of Array.from(
    doc.getElementsByTagNameNS(BPMNDI_NS, "BPMNDiagram"),
  )) {
    d.parentNode?.removeChild(d);
  }
  return new XMLSerializer().serializeToString(doc);
}

/** Aplica a geometria calculada ao snapshot: gera o fragmento BPMN-DI. */
export function buildDiXml(
  laidOut: ElkNode,
  snapshot: LayoutSnapshot,
  planeElementId: string,
): string {
  const { bounds, edgePoints, labels } = resolveGeometry(laidOut, snapshot);

  const labelXml = (id: string) => {
    const l = labels.get(id);
    return l
      ? `\n        <bpmndi:BPMNLabel id="lbl_${id}">\n          <dc:Bounds x="${round(l.x)}" y="${round(l.y)}" width="${round(l.width)}" height="${round(l.height)}"/>\n        </bpmndi:BPMNLabel>`
      : "";
  };

  const diagramId = `bpmndi_${Math.random().toString(36).slice(2, 10)}`;
  const planeId = `${diagramId}_plane`;

  const shapes = snapshot.nodes
    .filter((n) => bounds.has(n.id))
    .map((n) => {
      const b = bounds.get(n.id)!;
      return `      <bpmndi:BPMNShape id="shape_${n.id}" bpmnElement="${n.id}">\n        <dc:Bounds x="${round(b.x)}" y="${round(b.y)}" width="${round(b.width)}" height="${round(b.height)}"/>${labelXml(n.id)}\n      </bpmndi:BPMNShape>`;
    });

  const diEdges = snapshot.edges
    .filter((e) => edgePoints.has(e.id))
    .map((e) => {
      const pts = edgePoints.get(e.id)!
        .map((p) => `        <di:waypoint x="${round(p.x)}" y="${round(p.y)}"/>`)
        .join("\n");
      return `      <bpmndi:BPMNEdge id="edge_${e.id}" bpmnElement="${e.id}">\n${pts}${labelXml(e.id)}\n      </bpmndi:BPMNEdge>`;
    });

  return [
    `    <bpmndi:BPMNDiagram id="${diagramId}">`,
    `      <bpmndi:BPMNPlane id="${planeId}" bpmnElement="${planeElementId}">`,
    ...shapes,
    ...diEdges,
    `      </bpmndi:BPMNPlane>`,
    `    </bpmndi:BPMNDiagram>`,
  ].join("\n");
}

/** Insere o fragmento BPMN-DI antes de </definitions>. */
export function injectDiIntoXml(xml: string, diXml: string): string {
  const closing = /<\/(bpmn:|bpmn2:|)?definitions>\s*$/;
  if (!closing.test(xml)) return xml;
  return xml.replace(closing, `${diXml}\n</$1definitions>`);
}

/** Process/colaboração raiz para ligar o BPMNPlane. */
export function planeElementFor(xml: string): string | null {
  const doc = new DOMParser().parseFromString(xml, "application/xml");
  const collab = doc.getElementsByTagNameNS(BPMN_NS, "collaboration")[0];
  if (collab?.getAttribute("id")) return collab.getAttribute("id");
  const process = doc.getElementsByTagNameNS(BPMN_NS, "process")[0];
  return process?.getAttribute("id") ?? null;
}

function round(n: number): number {
  return Math.round(n * 100) / 100;
}
