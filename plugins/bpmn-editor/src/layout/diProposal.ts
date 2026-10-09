/**
 * DI proposal — aplica geometria ELK ao artefato BPMN produzindo
 * BPMNShape/BPMNEdge/BPMNPlane (P5 §15). Proposta é transient: o usuário
 * aceita (vira commands do editor → dirty) ou cancela (descartada).
 *
 * Snapshot/DI usam DOMParser puro — nunca APIs vendor fora de src/editor.
 */

import type { ElkNode } from "./elkGraph";
import type { LayoutSnapshot } from "./elkGraph";
import { LAYOUT_PROFILE_V1, containerPadFor } from "./layoutProfile";
import { fitTextSize, isTextFitNodeType } from "./textFit";

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

const CONTAINERS = new Set([
  "process",
  "subProcess",
  "transaction",
  "adHocSubProcess",
  "laneSet",
  "childLaneSet",
]);

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

/** SubProcess-family: filhos semânticos viram children ELK. */
const SUBPROCESS_FAMILY = new Set([
  "bpmn:subProcess",
  "bpmn:transaction",
  "bpmn:adHocSubProcess",
  "bpmn:eventSubProcess",
]);

function mayResize(node: LayoutSnapshot["nodes"][number]): boolean {
  if (node.isParticipant || node.isLane) return true;
  if (!RESIZABLE_CONTAINERS.has(node.type.replace(/^bpmn:/, ""))) return false;
  // collapsed subProcess não tem children visíveis → SIZE_PRESERVED.
  return node.isExpanded !== false;
}

/** G9 — text-fit: cresce bounds de elementos com label interna ANTES do
 *  ELK, para que espaçamento/posições já considerem o tamanho final.
 *  Grow-only: nunca encolhe bounds DI existentes maiores que o fit
 *  (sizing manual do usuário é respeitado). Containers com filhos
 *  (participant/lane/subProcess EXPANDIDO) ficam a cargo do ELK — só o
 *  subProcess COLLAPSED (label interna) entra no fit. Retorna o mesmo
 *  snapshot mutado — é um artefato efêmero por definição. */
export function applyTextFitSizing(snapshot: LayoutSnapshot): LayoutSnapshot {
  const cfg = LAYOUT_PROFILE_V1.textFit;
  for (const node of snapshot.nodes) {
    if (!isTextFitNodeType(node.type)) continue;
    if (SUBPROCESS_FAMILY.has(node.type) && node.isExpanded !== false) continue;
    const fit = fitTextSize(node.label ?? "");
    node.width = Math.max(node.width ?? cfg.minWidth, fit.width);
    node.height = Math.max(node.height ?? cfg.minHeight, fit.height);
  }
  return snapshot;
}

/** Piso de dimensão para containers RESIZABLE — ELK pode devolver menos
 *  que o mínimo legível quando o conteúdo é pequeno (G9 §3 lanes). */
function containerMinSize(
  node: LayoutSnapshot["nodes"][number],
): { width: number; height: number } | undefined {
  const min = LAYOUT_PROFILE_V1.containerMin;
  if (node.isParticipant) return min.participant;
  if (node.isLane) return min.lane;
  if (SUBPROCESS_FAMILY.has(node.type)) return min.subProcess;
  return undefined;
}

/** Extrai o snapshot de layout de um BPMN XML (sem DI necessário).
 *  Quando há BPMN-DI, captura os bounds atuais por bpmnElement —
 *  a fonte de verdade do tamanho é o DI vigente, não o default vendor.
 *
 *  Hierarquia ELK derivada da SEMÂNTICA BPMN vigente:
 *    participant.processRef → process
 *    process.laneSet.lane.flowNodeRef → membros da lane
 *    lane.childLaneSet.lane → lanes aninhadas
 *    subProcess.flowElements → filhos do subProcess expandido
 *  Elementos de processo sem lane → filhos do participant
 *  (PROCESS_LEVEL_UNLANED — nunca atribuídos a uma lane indevida). */
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
  /** Todos os atributos DI do elemento além de id/bpmnElement —
   *  preservados verbatim no preview (isExpanded, isHorizontal, cores…). */
  const readDiAttrs = (diEl: Element) => {
    const attrs: Record<string, string> = {};
    for (const attr of Array.from(diEl.attributes)) {
      if (attr.name !== "id" && attr.name !== "bpmnElement") {
        attrs[attr.name] = attr.value;
      }
    }
    return attrs;
  };

  const diSize = new Map<
    string,
    {
      x: number;
      y: number;
      width: number;
      height: number;
      label?: DiBounds;
      isExpanded?: boolean;
      diId?: string;
      diAttrs: Record<string, string>;
    }
  >();
  for (const shape of Array.from(
    doc.getElementsByTagNameNS(BPMNDI_NS, "BPMNShape"),
  )) {
    const ref = shape.getAttribute("bpmnElement");
    const b = readBounds(
      shape.getElementsByTagNameNS(DC_NS, "Bounds")[0],
    );
    const expandedAttr = shape.getAttribute("isExpanded");
    if (ref) {
      diSize.set(ref, {
        x: b?.x ?? NaN,
        y: b?.y ?? NaN,
        width: b?.width ?? NaN,
        height: b?.height ?? NaN,
        label: readLabel(shape),
        isExpanded:
          expandedAttr === "true" ? true : expandedAttr === "false" ? false : undefined,
        diId: shape.getAttribute("id") ?? undefined,
        diAttrs: readDiAttrs(shape),
      });
    }
  }
  const diEdge = new Map<
    string,
    {
      points: { x: number; y: number }[];
      label?: DiBounds;
      diId?: string;
      diAttrs: Record<string, string>;
    }
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
    if (ref) {
      diEdge.set(ref, {
        points,
        label: readLabel(edge),
        diId: edge.getAttribute("id") ?? undefined,
        diAttrs: readDiAttrs(edge),
      });
    }
  }

  const localName = (el: Element) => el.localName || el.tagName.split(":").pop() || "";

  // Membership semântica coletada durante o walk.
  const poolForProcess = new Map<string, string>(); // processId → participantId
  const laneOwnerProcess = new Map<string, string>(); // laneId → processId
  const laneMembers = new Map<string, Set<string>>(); // laneId → flowNodeRef ids
  const nodeProcess = new Map<string, string>(); // nodeId → processId

  const walk = (el: Element, parentId?: string, processId?: string) => {
    for (const child of Array.from(el.children)) {
      const name = localName(child);
      // Containers semânticos são atravessados mesmo sem id próprio
      // (laneSet/childLaneSet id é opcional no BPMN).
      if (name === "process") {
        const pid = child.getAttribute("id");
        walk(child, parentId, pid ?? processId);
        continue;
      }
      if (
        (CONTAINERS.has(name) && !SUBPROCESS_FAMILY.has(`bpmn:${name}`)) ||
        name === "collaboration" ||
        name === "definitions"
      ) {
        walk(child, parentId, processId);
        continue;
      }
      const id = child.getAttribute("id");
      if (!id) continue;
      if (FLOW_NODES.has(name)) {
        const size = diSize.get(id);
        nodes.push({
          id,
          type: `bpmn:${name}`,
          label: child.getAttribute("name") ?? undefined,
          parentId,
          x: size ? size.x : undefined,
          y: size ? size.y : undefined,
          width: size ? size.width : undefined,
          height: size ? size.height : undefined,
          labelBounds: size?.label,
          isExpanded: size?.isExpanded,
          diId: size?.diId,
          diAttrs: size?.diAttrs,
          isBoundary: name === "boundaryEvent",
          attachedToId: child.getAttribute("attachedToRef") ?? undefined,
          isLane: name === "lane",
          isParticipant: name === "participant",
        });
        if (processId) nodeProcess.set(id, processId);
        if (name === "lane") {
          if (processId) laneOwnerProcess.set(id, processId);
          const members = new Set<string>();
          for (const ref of Array.from(child.children)) {
            if (localName(ref) === "flowNodeRef" && ref.textContent) {
              members.add(ref.textContent.trim());
            }
          }
          laneMembers.set(id, members);
        } else if (name === "participant") {
          const ref = child.getAttribute("processRef");
          if (ref) poolForProcess.set(ref, id);
        }
        walk(child, id, processId);
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
            diId: di?.diId,
            diAttrs: di?.diAttrs,
          });
        }
      }
    }
  };
  walk(doc.documentElement);

  // Deriva o parentId de layout a partir da semântica BPMN:
  // lane.flowNodeRef e participant.processRef dirigem o containment.
  const nodeById = new Map(nodes.map((n) => [n.id, n]));
  const memberLane = new Map<string, string>();
  for (const [laneId, members] of laneMembers) {
    for (const m of members) if (nodeById.has(m)) memberLane.set(m, laneId);
  }

  for (const node of nodes) {
    if (node.isParticipant) {
      node.parentId = undefined;
      continue;
    }
    const semParent = node.parentId ? nodeById.get(node.parentId) : undefined;
    if (node.isLane) {
      // Lane aninhada mantém a lane pai; lane raiz vai para o pool.
      if (semParent?.isLane) continue;
      node.parentId =
        poolForProcess.get(laneOwnerProcess.get(node.id) ?? "") ?? undefined;
      continue;
    }
    // Filho semântico de subProcess expandido permanece dentro dele.
    if (semParent && SUBPROCESS_FAMILY.has(semParent.type)) continue;
    const lane = memberLane.get(node.id);
    if (lane) {
      node.parentId = lane;
      continue;
    }
    // PROCESS_LEVEL_UNLANED — região do participant, nunca numa lane.
    node.parentId =
      poolForProcess.get(nodeProcess.get(node.id) ?? "") ?? undefined;
  }
  // Boundary events seguem o parent resolvido do host.
  for (const node of nodes) {
    if (!node.isBoundary || !node.attachedToId) continue;
    const host = nodeById.get(node.attachedToId);
    if (host) node.parentId = host.parentId;
  }

  // bpmn:group — artifact VISUAL (Group não é container semântico:
  // sem flowNodeRef/children). A relação de enclosure é derivada do
  // BPMN-DI corrente por containment geométrico total e vive apenas
  // no snapshot efêmero — o XML semântico nunca recebe membership.
  const hasDiBounds = (n: (typeof nodes)[number]): n is (typeof nodes)[number] & { x: number; y: number; width: number; height: number } =>
    n.x != null && n.y != null && n.width != null && n.height != null;
  const fullyInside = (
    inner: (typeof nodes)[number],
    outer: (typeof nodes)[number],
  ): boolean => {
    if (!hasDiBounds(inner) || !hasDiBounds(outer)) return false;
    return (
      inner.x >= outer.x &&
      inner.y >= outer.y &&
      inner.x + inner.width <= outer.x + outer.width &&
      inner.y + inner.height <= outer.y + outer.height
    );
  };
  for (const group of nodes.filter((n) => n.type === "bpmn:group")) {
    group.visualMembers = nodes
      .filter((n) => n.id !== group.id && fullyInside(n, group))
      .map((n) => n.id)
      .sort();
  }

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

/** Translação acumulada por nó durante o container-fit — registra quanto
 *  cada subtree se moveu para que edges possam decidir entre
 *  shift-preserving (endpoints moveram juntos) e re-route orthogonal. */
type NodeShift = { dx: number; dy: number };

/** Container-fit bottom-up (G9-LAYOUT-1 §1): calcula bounds de cada
 *  container a partir do bounding box REAL dos filhos já posicionados
 *  pelo ELK + padding governado do profile. Processa do mais profundo
 *  para o mais raso — lane aninhada antes da lane pai, subprocess antes
 *  da lane, lanes antes do participant. Nunca encolhe container abaixo
 *  do `containerMin`; children invadindo a reserva de header são
 *  transladados (subtree inteira), nunca o legado.
 *
 *  Composição BPMN aplicada aqui (elk.layered posiciona siblings lado a
 *  lado, não produz lane-stacking): lanes irmãs empilham flush na ordem
 *  de declaração do XML e compartilham a largura interna do participant;
 *  membros unlaned ficam numa região abaixo da stack; participants irmãos
 *  na raiz empilham verticalmente com `poolGap`.
 *
 *  Retorna o mapa de shifts para revalidação de waypoints de edges. */
function fitContainersToContent(
  geometry: LayoutGeometry,
  snapshot: LayoutSnapshot,
): Map<string, NodeShift> {
  const bounds = geometry.bounds;
  const byId = new Map(snapshot.nodes.map((n) => [n.id, n]));
  const docOrder = new Map(snapshot.nodes.map((n, i) => [n.id, i]));

  const childrenOf = new Map<string, string[]>();
  for (const n of snapshot.nodes) {
    if (!n.parentId || !bounds.has(n.id)) continue;
    const list = childrenOf.get(n.parentId) ?? [];
    list.push(n.id);
    childrenOf.set(n.parentId, list);
  }

  const shifts = new Map<string, NodeShift>();
  const shiftNode = (id: string, dx: number, dy: number) => {
    const b = bounds.get(id);
    if (b) {
      b.x += dx;
      b.y += dy;
    }
    const s = shifts.get(id) ?? { dx: 0, dy: 0 };
    s.dx += dx;
    s.dy += dy;
    shifts.set(id, s);
  };
  const translateSubtree = (id: string, dx: number, dy: number) => {
    if (!dx && !dy) return;
    shiftNode(id, dx, dy);
    for (const kid of childrenOf.get(id) ?? []) translateSubtree(kid, dx, dy);
  };

  const depthMemo = new Map<string, number>();
  const depthOf = (id: string): number => {
    const memo = depthMemo.get(id);
    if (memo != null) return memo;
    let d = 0;
    let p = byId.get(id)?.parentId;
    while (p) {
      d += 1;
      p = byId.get(p)?.parentId;
    }
    depthMemo.set(id, d);
    return d;
  };

  const isFitContainer = (n: LayoutSnapshot["nodes"][number]) =>
    bounds.has(n.id) &&
    (n.isParticipant ||
      n.isLane ||
      (SUBPROCESS_FAMILY.has(n.type) && n.isExpanded !== false));

  const padsFor = (n: LayoutSnapshot["nodes"][number]) =>
    containerPadFor(
      n.isParticipant
        ? "participant"
        : n.isLane
          ? "lane"
          : SUBPROCESS_FAMILY.has(n.type)
            ? "subprocess"
            : "default",
    );

  const containers = snapshot.nodes
    .filter(isFitContainer)
    .sort(
      (a, b) =>
        depthOf(b.id) - depthOf(a.id) ||
        (docOrder.get(a.id) ?? 0) - (docOrder.get(b.id) ?? 0),
    );

  for (const c of containers) {
    const b = bounds.get(c.id)!;
    const pads = padsFor(c);
    const min = containerMinSize(c) ?? { width: 0, height: 0 };
    const kids = (childrenOf.get(c.id) ?? []).filter((id) => bounds.has(id));

    if (!kids.length) {
      b.width = Math.max(b.width, min.width);
      b.height = Math.max(b.height, min.height);
      continue;
    }

    const lanes = kids
      .filter((id) => byId.get(id)?.isLane)
      .sort((a, b2) => (docOrder.get(a) ?? 0) - (docOrder.get(b2) ?? 0));
    const others = kids.filter((id) => !byId.get(id)?.isLane);

    const contentX = b.x + pads.left;
    const contentTop = b.y + pads.top;
    let cursorY = contentTop;

    // Lane stack: flush vertical na ordem do documento, alinhadas ao
    // content origin. Filhos da lane movem junto (subtree).
    for (const laneId of lanes) {
      const lb = bounds.get(laneId)!;
      translateSubtree(laneId, contentX - lb.x, cursorY - lb.y);
      cursorY += lb.height;
    }

    // Membros não-lane (PROCESS_LEVEL_UNLANED dentro de participant,
    // ou filhos diretos de subprocess/lane): região abaixo da stack de
    // lanes (ou content top), nunca sobrepondo a reserva de header.
    if (others.length) {
      const minX = Math.min(...others.map((id) => bounds.get(id)!.x));
      const minY = Math.min(...others.map((id) => bounds.get(id)!.y));
      const targetY = lanes.length
        ? cursorY + LAYOUT_PROFILE_V1.unlanedGap
        : contentTop;
      const dx = Math.max(0, contentX - minX);
      const dy = Math.max(0, targetY - minY);
      for (const id of others) translateSubtree(id, dx, dy);
    }

    // Fit: container cobre o bounding box real dos filhos + padding.
    const right = Math.max(
      ...kids.map((id) => bounds.get(id)!.x + bounds.get(id)!.width),
    );
    const bottom = Math.max(
      ...kids.map((id) => bounds.get(id)!.y + bounds.get(id)!.height),
    );
    b.width = Math.max(b.width, min.width, right + pads.right - b.x);
    b.height = Math.max(b.height, min.height, bottom + pads.bottom - b.y);

    // Lanes irmãs compartilham a largura interna do container pai —
    // uma lane nunca é mais estreita que suas irmãs (§17).
    const innerW = b.width - pads.left - pads.right;
    for (const laneId of lanes) {
      bounds.get(laneId)!.width = innerW;
    }
  }

  // Lanes sem participant (processo sem collaboration): mesmo stack na
  // raiz — x/largura compartilhados, flush vertical na ordem do documento.
  const rootLanes = snapshot.nodes
    .filter((n) => !n.parentId && n.isLane && bounds.has(n.id))
    .sort((a, b) => (docOrder.get(a.id) ?? 0) - (docOrder.get(b.id) ?? 0));
  if (rootLanes.length > 0) {
    const x0 = Math.min(...rootLanes.map((l) => bounds.get(l.id)!.x));
    const w = Math.max(...rootLanes.map((l) => bounds.get(l.id)!.width));
    let y = Math.min(...rootLanes.map((l) => bounds.get(l.id)!.y));
    for (const l of rootLanes) {
      const lb = bounds.get(l.id)!;
      translateSubtree(l.id, x0 - lb.x, y - lb.y);
      lb.width = w;
      y += lb.height;
    }
  }

  // Participants irmãos na raiz: mesma x/largura, stack vertical.
  const pools = snapshot.nodes
    .filter((n) => !n.parentId && n.isParticipant && bounds.has(n.id))
    .sort((a, b) => (docOrder.get(a.id) ?? 0) - (docOrder.get(b.id) ?? 0));
  if (pools.length > 0) {
    const minX = Math.min(...pools.map((p) => bounds.get(p.id)!.x));
    const w = Math.max(...pools.map((p) => bounds.get(p.id)!.width));
    let y = Math.min(...pools.map((p) => bounds.get(p.id)!.y));
    for (const p of pools) {
      const pb = bounds.get(p.id)!;
      translateSubtree(p.id, minX - pb.x, y - pb.y);
      pb.width = w;
      y += pb.height + LAYOUT_PROFILE_V1.poolGap;
    }
  }

  return shifts;
}

/** Ancestor de containment mais próximo (lane/participant); o próprio
 *  endpoint quando ele já é um container. */
function containerAncestor(
  id: string,
  byId: Map<string, LayoutSnapshot["nodes"][number]>,
): string | undefined {
  let cur = byId.get(id);
  while (cur) {
    if (cur.isLane || cur.isParticipant) return cur.id;
    cur = cur.parentId ? byId.get(cur.parentId) : undefined;
  }
  return undefined;
}

/** Rota orthogonal mínima entre bounds finais — usada apenas para
 *  edges cujos endpoints cruzam fronteira de lane/pool (pontos ELK
 *  dessas edges ficam obsoletos quando a stack é normalizada). */
function routeOrthogonal(
  a: DiBounds,
  b: DiBounds,
): Array<{ x: number; y: number }> {
  const ac = { x: a.x + a.width / 2, y: a.y + a.height / 2 };
  const bc = { x: b.x + b.width / 2, y: b.y + b.height / 2 };
  const dx = bc.x - ac.x;
  const dy = bc.y - ac.y;
  if (Math.abs(dy) > Math.abs(dx)) {
    const s = { x: ac.x, y: dy > 0 ? a.y + a.height : a.y };
    const t = { x: bc.x, y: dy > 0 ? b.y : b.y + b.height };
    const my = (s.y + t.y) / 2;
    return [s, { x: s.x, y: my }, { x: t.x, y: my }, t];
  }
  const s = { x: dx > 0 ? a.x + a.width : a.x, y: ac.y };
  const t = { x: dx > 0 ? b.x : b.x + b.width, y: bc.y };
  const mx = (s.x + t.x) / 2;
  return [s, { x: mx, y: s.y }, { x: mx, y: t.y }, t];
}

/** Geometria final: posições ELK + width/height vigentes para nós que
 *  não podem ser redimensionados pelo layout (SIZE_PRESERVED).
 *  Containers (pool/lane/subProcess expandido) mantêm o tamanho ELK. */
function resolveGeometry(
  laidOut: ElkNode,
  snapshot: LayoutSnapshot,
): LayoutGeometry {
  const byId = new Map(snapshot.nodes.map((n) => [n.id, n]));

  const geometry = computeGeometry(laidOut);
  for (const [id, b] of geometry.bounds) {
    const node = byId.get(id);
    if (!node) continue;
    if (!mayResize(node)) {
      if (node.width != null && node.height != null) {
        b.width = node.width;
        b.height = node.height;
      }
      continue;
    }
    // Container resizable: piso legível — nunca abaixo do containerMin.
    const min = containerMinSize(node);
    if (min) {
      b.width = Math.max(b.width, min.width);
      b.height = Math.max(b.height, min.height);
    }
  }

  // G9-LAYOUT-1: container-fit bottom-up em coordenadas absolutas —
  // containers crescem a partir do bounding box REAL dos filhos já
  // dimensionados (text-fit) e posicionados (ELK), respeitando a reserva
  // de header e o padding governado. Substitui a normalização na árvore
  // ELK: lanes empilham/alinham, participants englobam, subprocessos
  // expandidos ajustam — recursivo por profundidade.
  const shifts = fitContainersToContent(geometry, snapshot);

  // bpmn:group — artifact visual fora do ELK. Re-bounds: bounding box
  // dos visualMembers (enclosure derivado do DI pré-layout) + padding
  // do profile. Preserva a INTENÇÃO VISUAL do usuário sem tocar na
  // semântica. Iterativo para grupos aninhados (grupo membro de grupo
  // resolve de dentro para fora). Grupo vazio ou não resolvível mantém
  // os bounds DI originais — nunca perde o shape no preview.
  const preserveDiBounds = (group: (typeof snapshot.nodes)[number]) => {
    if (
      group.x != null &&
      group.y != null &&
      group.width != null &&
      group.height != null
    ) {
      geometry.bounds.set(group.id, {
        x: group.x,
        y: group.y,
        width: group.width,
        height: group.height,
      });
    }
  };
  const groups = snapshot.nodes.filter((n) => n.type === "bpmn:group");
  const pending = new Map(groups.map((g) => [g.id, g]));
  for (let pass = 0; pass <= groups.length && pending.size; pass++) {
    let progressed = false;
    for (const [gid, group] of pending) {
      const members = group.visualMembers ?? [];
      if (!members.length) {
        preserveDiBounds(group);
        pending.delete(gid);
        progressed = true;
        continue;
      }
      const memberBounds = members.map((id) => geometry.bounds.get(id));
      if (memberBounds.some((b) => !b)) continue; // member oculto/pendente
      const xs = memberBounds.map((b) => b!.x);
      const ys = memberBounds.map((b) => b!.y);
      const x2 = Math.max(...memberBounds.map((b) => b!.x + b!.width));
      const y2 = Math.max(...memberBounds.map((b) => b!.y + b!.height));
      const pad = LAYOUT_PROFILE_V1.groupPadding;
      geometry.bounds.set(gid, {
        x: Math.min(...xs) - pad,
        y: Math.min(...ys) - pad,
        width: x2 - Math.min(...xs) + pad * 2,
        height: y2 - Math.min(...ys) + pad * 2,
      });
      pending.delete(gid);
      progressed = true;
    }
    if (!progressed) break;
  }
  for (const [, group] of pending) preserveDiBounds(group);

  // Revalidação de waypoints pós-fit (§27): endpoints que transladaram
  // JUNTOS preservam a rota ELK (shift puro nos pontos); endpoints com
  // shifts diferentes — ou que cruzam fronteira de container — recebem
  // rota orthogonal entre os bounds finais.
  for (const edge of snapshot.edges) {
    const pts = geometry.edgePoints.get(edge.id);
    if (!pts) continue;
    const a = geometry.bounds.get(edge.sourceId);
    const b = geometry.bounds.get(edge.targetId);
    if (!a || !b) continue;
    const sShift = shifts.get(edge.sourceId);
    const tShift = shifts.get(edge.targetId);
    const sameShift =
      sShift == null && tShift == null
        ? true
        : sShift != null &&
          tShift != null &&
          sShift.dx === tShift.dx &&
          sShift.dy === tShift.dy;
    const crossContainer =
      containerAncestor(edge.sourceId, byId) !==
      containerAncestor(edge.targetId, byId);
    if (sameShift && !crossContainer) {
      if (sShift) {
        for (const p of pts) {
          p.x += sShift.dx;
          p.y += sShift.dy;
        }
      }
    } else {
      geometry.edgePoints.set(edge.id, routeOrthogonal(a, b));
    }
  }

  // Edges fora do grafo ELK (ex.: association → bpmn:group): quando um
  // endpoint transladou no fit, os waypoints DI originais estão obsoletos
  // → rota orthogonal entre bounds finais (§27 — inclui associations).
  for (const edge of snapshot.edges) {
    if (geometry.edgePoints.has(edge.id)) continue;
    const sShift = shifts.get(edge.sourceId);
    const tShift = shifts.get(edge.targetId);
    const moved =
      (sShift != null && (sShift.dx !== 0 || sShift.dy !== 0)) ||
      (tShift != null && (tShift.dx !== 0 || tShift.dy !== 0));
    if (!moved) continue;
    const a = geometry.bounds.get(edge.sourceId);
    const b = geometry.bounds.get(edge.targetId);
    if (!a || !b) continue;
    geometry.edgePoints.set(edge.id, routeOrthogonal(a, b));
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

  const attrsXml = (attrs?: Record<string, string>) => {
    const entries = Object.entries(attrs ?? {});
    return entries.length
      ? " " +
          entries
            .map(([k, v]) => `${k}="${escapeXmlAttr(v)}"`)
            .join(" ")
      : "";
  };

  const shapes = snapshot.nodes
    .filter((n) => bounds.has(n.id))
    .map((n) => {
      const b = bounds.get(n.id)!;
      return `      <bpmndi:BPMNShape id="${n.diId ?? `shape_${n.id}`}" bpmnElement="${n.id}"${attrsXml(n.diAttrs)}>\n        <dc:Bounds x="${round(b.x)}" y="${round(b.y)}" width="${round(b.width)}" height="${round(b.height)}"/>${labelXml(n.id)}\n      </bpmndi:BPMNShape>`;
    });

  const diEdges = snapshot.edges
    .filter((e) => edgePoints.has(e.id))
    .map((e) => {
      const pts = edgePoints.get(e.id)!
        .map((p) => `        <di:waypoint x="${round(p.x)}" y="${round(p.y)}"/>`)
        .join("\n");
      return `      <bpmndi:BPMNEdge id="${e.diId ?? `edge_${e.id}`}" bpmnElement="${e.id}"${attrsXml(e.diAttrs)}>\n${pts}${labelXml(e.id)}\n      </bpmndi:BPMNEdge>`;
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

function escapeXmlAttr(v: string): string {
  return v
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}
