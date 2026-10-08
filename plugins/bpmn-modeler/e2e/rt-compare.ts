/**
 * G4 — comparador estrutural BPMN XML (test-only, nunca production domain).
 *
 * Implementa SEMANTICALLY_EQUIVALENT + DI_EQUIVALENT + EXTENSION_EQUIVALENT
 * (BPMN-INTEROPERABILITY-SPEC-FREEZE §18) como utilitário de evidência:
 *
 *   - compara expanded QName (ns-uri + local) — nunca prefix textual;
 *   - compara atributos como mapa (ordem irrelevante), com resolução de
 *     valores QName tipados via nsmap in-scope;
 *   - compara texto normalizado (whitespace colapsado);
 *   - compara filhos: multiset por identidade (qname + id/bpmnElement);
 *     filhos sem identidade (Bounds, waypoint, text, documentation...)
 *     são pareados por ordem dentro do mesmo qname;
 *   - dentro de `extensionElements` a comparação de filhos é ORDENADA
 *     (ordem pode ser semântica para o vendor da extensão);
 *   - coordenadas DI (x/y/width/height) comparadas numericamente.
 *
 * Normalização explicitamente permitida (SPEC §14/§38): whitespace,
 * ordem de atributos, spelling de prefixo, declaração XML.
 * Também ignorados no root `<definitions>`: `exporter`/`exporterVersion`
 * — metadados de proveniência do serializer, sobrescritos por bpmn-js
 * a cada export (EXPECTED_SERIALIZATION_DIFF, não conteúdo do modelo).
 *
 * Elisão de atributo com valor-default: bpmn-moddle omite do XML attrs
 * cujo valor igual ao default BPMN 2.0/XSD (ex.: isCollection="false",
 * instantiate="false"). "ausente" ≡ "valor default" → equivalência
 * documentada em XSD_DEFAULTS (derivado dos XSDs vendored OMG).
 *
 * Normalização DERIVADA documentada: `<bpmn:incoming>`/`<bpmn:outgoing>`
 * são refs redundantes regeneradas pelo serializer do vendor a partir de
 * `sourceRef`/`targetRef` das connections — são removidas da árvore
 * canônica, MAS cada declaração é conferida contra as refs derivadas dos
 * flows (checkIncomingOutgoingConsistency): declaração que inventa ou
 * contradiz ref de flow vira diff REF_INCONSISTENCY. A fonte canônica
 * (sourceRef/targetRef na própria connection) é comparada estritamente.
 *
 * Nunca normalizados: ids, eventDefinitions, extensions, DI, refs.
 */
import { JSDOM } from "jsdom";

const BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL";
const XSI = "http://www.w3.org/2001/XMLSchema-instance";

/** Atributos cujo valor é QName (resolver prefixo → URI in-scope). */
const QNAME_ATTRS = new Set([
  "type",
  "sourceRef",
  "targetRef",
  "attachedToRef",
  "processRef",
  "default",
  "bpmnElement",
  "calledElement",
  "calledChoreographyRef",
  "calledCollaborationRef",
  "eventDefinitionRef",
  "messageRef",
  "signalRef",
  "errorRef",
  "escalationRef",
  "cancelEventDefinitionRef",
  "itemSubjectRef",
  "categoryValueRef",
  "evaluatesToTypeRef",
  "supportedInterfaceRef",
  "structureRef",
  "itemKind",
  "definition",
  "operationRef",
  "implementationRef",
  "resourceRef",
  "dataStoreRef",
  "dataObjectRef",
  "dataInputRefs",
  "dataOutputRefs",
  "inputSetRefs",
  "outputSetRefs",
  "rootElement",
  "processType",
]);

/** Attrs numéricos DI — comparação como double (tolerância serializer). */
const NUMERIC_ATTRS = new Set(["x", "y", "width", "height"]);

/**
 * Defaults BPMN 2.0/XSD por local name de atributo — atributo ausente é
 * semanticamente equivalente ao valor default (bpmn-moddle elide ao
 * serializar). Fonte: XSDs vendored (Semantic.xsd/BPMNDI.xsd).
 */
const XSD_DEFAULTS = new Map<string, string>([
  ["isCollection", "false"],
  ["instantiate", "false"],
  ["eventGatewayType", "Exclusive"],
  ["cancelRemainingInstances", "true"],
  ["waitForCompletion", "true"],
  ["isInterrupting", "true"],
  ["testBefore", "false"],
  ["isSequential", "false"],
  ["mustUnderstand", "false"],
  ["cancelActivity", "true"],
  ["parallelMultiple", "false"],
  ["triggeredByEvent", "false"],
  ["isForCompensation", "false"],
  ["isExecutable", "false"],
  ["associationDirection", "None"],
  ["isClosed", "false"],
  ["processType", "None"],
  ["startQuantity", "1"],
  ["completionQuantity", "1"],
  ["loopType", "None"],
  ["gatewayDirection", "Unspecified"],
  ["itemKind", "Information"],
]);

/** Filhos comparados ORDENADOS (ordem significativa / desconhecida). */
const ORDERED_PARENT_LOCAL = new Set(["extensionElements"]);

/** Elementos derivados removidos da árvore canônica (ver doc acima). */
const DERIVED_LOCAL = new Set(["incoming", "outgoing"]);

export type CanonEl = {
  /** "{ns-uri}local" */
  qname: string;
  attrs: Map<string, string>;
  text: string;
  children: CanonEl[];
};

export type Diff = {
  kind:
    | "MISSING_ELEMENT"
    | "EXTRA_ELEMENT"
    | "QNAME_DIFF"
    | "ATTR_DIFF"
    | "TEXT_DIFF"
    | "REF_INCONSISTENCY"
    | "PARSE_ERROR";
  path: string;
  detail: string;
};

function normText(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

function qnameOf(el: { namespaceURI: string | null; localName: string | null }) {
  return `{${el.namespaceURI ?? ""}}${el.localName ?? ""}`;
}

function resolveQNameValue(el: Element, raw: string): string {
  // lista de QNames separados por espaço (ex.: dataInputRefs)
  if (/\s/.test(raw.trim())) {
    return raw
      .trim()
      .split(/\s+/)
      .map((v) => resolveQNameValue(el, v))
      .join(" ");
  }
  const m = /^([A-Za-z_][\w.-]*):([\w.$-]+)$/.exec(raw);
  if (!m) return raw;
  const ns = el.lookupNamespaceURI(m[1]);
  return ns ? `{${ns}}${m[2]}` : raw;
}

function canonize(el: Element): CanonEl {
  const node: CanonEl = { qname: qnameOf(el), attrs: new Map(), text: "", children: [] };
  const isDefinitions = el.namespaceURI === BPMN && el.localName === "definitions";
  for (const attr of Array.from(el.attributes)) {
    if (attr.namespaceURI === "http://www.w3.org/2000/xmlns/") continue;
    if (attr.prefix === "xmlns" || attr.name === "xmlns") continue;
    if (
      isDefinitions &&
      (attr.localName === "exporter" || attr.localName === "exporterVersion")
    )
      continue;
    const key = `{${attr.namespaceURI ?? ""}}${attr.localName ?? attr.name}`;
    let value = attr.value;
    if (
      QNAME_ATTRS.has(attr.localName ?? "") ||
      (attr.namespaceURI === XSI && attr.localName === "type")
    ) {
      value = resolveQNameValue(el, value);
    }
    if (NUMERIC_ATTRS.has(attr.localName ?? "") && /^-?[\d.eE+-]+$/.test(value)) {
      value = String(Number(value));
    }
    node.attrs.set(key, value);
  }
  const texts: string[] = [];
  for (const child of Array.from(el.childNodes)) {
    if (child.nodeType === 3 || child.nodeType === 4) {
      const t = normText(child.nodeValue ?? "");
      if (t) texts.push(t);
    } else if (child.nodeType === 1) {
      const cel = child as Element;
      const isDerived =
        cel.namespaceURI === BPMN && DERIVED_LOCAL.has(cel.localName ?? "");
      if (!isDerived) node.children.push(canonize(cel));
    }
    // comments(8)/PI(7): não-semânticos (SPEC §38) — ignorados
  }
  node.text = texts.join(" ");
  return node;
}

/** Chave de identidade para pareamento multiset de filhos. */
function identityOf(el: CanonEl): string | null {
  for (const k of [
    `{${""}}id`,
    "{http://www.omg.org/spec/BPMN/20100524/DI}bpmnElement",
    "{}bpmnElement",
  ]) {
    const v = el.attrs.get(k);
    if (v) return v;
  }
  return null;
}

export function parseCanon(xml: string): CanonEl {
  const dom = new JSDOM("");
  const doc = new dom.window.DOMParser().parseFromString(
    xml,
    "application/xml",
  );
  const err = doc.querySelector("parsererror");
  if (err) throw new Error(`XML parse error: ${normText(err.textContent ?? "")}`);
  return canonize(doc.documentElement);
}

function pathOf(parentPath: string, el: CanonEl): string {
  const id = identityOf(el);
  return `${parentPath}/${el.qname}${id ? `#${id}` : ""}`;
}

/** local de uma key "{ns}local"; ns ignora (attr no-ns = "{}local"). */
function localOf(key: string): string {
  return key.slice(key.indexOf("}") + 1);
}

function isDefaultValue(key: string, value: string): boolean {
  return XSD_DEFAULTS.get(localOf(key)) === value;
}

function compareAttrs(
  a: CanonEl,
  b: CanonEl,
  path: string,
  diffs: Diff[],
): void {
  for (const [k, va] of a.attrs) {
    const vb = b.attrs.get(k);
    if (vb === undefined) {
      // elisão de default XSD — equivalente, não é perda
      if (isDefaultValue(k, va)) continue;
      diffs.push({ kind: "ATTR_DIFF", path, detail: `attr ${k}="${va}" ausente` });
    } else if (va !== vb) {
      diffs.push({
        kind: "ATTR_DIFF",
        path,
        detail: `attr ${k}: "${va}" != "${vb}"`,
      });
    }
  }
  for (const [k, vb] of b.attrs) {
    if (!a.attrs.has(k)) {
      if (isDefaultValue(k, vb)) continue;
      diffs.push({ kind: "ATTR_DIFF", path, detail: `attr ${k}="${vb}" extra` });
    }
  }
}

function compareChildren(
  a: CanonEl,
  b: CanonEl,
  path: string,
  diffs: Diff[],
): void {
  const ordered = ORDERED_PARENT_LOCAL.has(
    a.qname.slice(a.qname.indexOf("}") + 1),
  );
  if (ordered) {
    const n = Math.max(a.children.length, b.children.length);
    for (let i = 0; i < n; i++) {
      const ca = a.children[i];
      const cb = b.children[i];
      if (ca && !cb) {
        diffs.push({
          kind: "MISSING_ELEMENT",
          path: pathOf(path, ca),
          detail: "elemento de extensão ausente (ordenado)",
        });
      } else if (!ca && cb) {
        diffs.push({
          kind: "EXTRA_ELEMENT",
          path: pathOf(path, cb),
          detail: "elemento de extensão extra (ordenado)",
        });
      } else {
        compareEl(ca!, cb!, pathOf(path, ca!), diffs);
      }
    }
    return;
  }
  // multiset: agrupa por (qname|identity)
  const groups = (list: CanonEl[]) => {
    const map = new Map<string, CanonEl[]>();
    for (const c of list) {
      const key = `${c.qname}#${identityOf(c) ?? ""}`;
      map.set(key, [...(map.get(key) ?? []), c]);
    }
    return map;
  };
  const ga = groups(a.children);
  const gb = groups(b.children);
  const keys = new Set([...ga.keys(), ...gb.keys()]);
  for (const key of [...keys].sort()) {
    const la = ga.get(key) ?? [];
    const lb = gb.get(key) ?? [];
    if (la.length === 1 && lb.length === 1 && identityOf(la[0])) {
      compareEl(la[0], lb[0], pathOf(path, la[0]), diffs);
      continue;
    }
    const n = Math.max(la.length, lb.length);
    for (let i = 0; i < n; i++) {
      const ca = la[i];
      const cb = lb[i];
      const label = pathOf(path, ca ?? cb!);
      if (ca && !cb) {
        diffs.push({
          kind: "MISSING_ELEMENT",
          path: label,
          detail: `ausente (count ${la.length}→${lb.length})`,
        });
      } else if (!ca && cb) {
        diffs.push({
          kind: "EXTRA_ELEMENT",
          path: label,
          detail: `extra (count ${la.length}→${lb.length})`,
        });
      } else {
        compareEl(ca!, cb!, label, diffs);
      }
    }
  }
}

function compareEl(a: CanonEl, b: CanonEl, path: string, diffs: Diff[]): void {
  if (a.qname !== b.qname) {
    diffs.push({
      kind: "QNAME_DIFF",
      path,
      detail: `${a.qname} != ${b.qname}`,
    });
    return;
  }
  compareAttrs(a, b, path, diffs);
  if (a.text !== b.text) {
    diffs.push({
      kind: "TEXT_DIFF",
      path,
      detail: `text "${a.text}" != "${b.text}"`,
    });
  }
  compareChildren(a, b, path, diffs);
}

/**
 * Consistência de refs derivadas (roda sobre o DOM cru — incoming/outgoing
 * são strippados da árvore canônica). Cada `<bpmn:incoming>`/`outgoing>`
 * declarado deve ser respaldado por um sequenceFlow real cujo endpoint seja
 * o elemento (declared ⊆ derived). Ref inventada → REF_INCONSISTENCY.
 */
export function checkIncomingOutgoingConsistency(xml: string): Diff[] {
  const diffs: Diff[] = [];
  const dom = new JSDOM("");
  const doc = new dom.window.DOMParser().parseFromString(
    xml,
    "application/xml",
  );
  const allEls = Array.from(
    doc.getElementsByTagNameNS(BPMN, "*"),
  ) as unknown as Element[];
  const flows = new Map<string, { src: string; tgt: string }>();
  for (const f of allEls) {
    if (
      f.localName === "sequenceFlow" ||
      f.localName === "messageFlow" ||
      f.localName === "association" ||
      f.localName === "dataInputAssociation" ||
      f.localName === "dataOutputAssociation"
    ) {
      const id = f.getAttribute("id");
      const src = f.getAttribute("sourceRef");
      const tgt = f.getAttribute("targetRef");
      if (id && src && tgt) flows.set(id, { src, tgt });
    }
  }
  for (const el of allEls) {
    const elId = el.getAttribute("id");
    if (!elId) continue;
    for (const child of Array.from(el.children) as unknown as Element[]) {
      if (
        child.namespaceURI !== BPMN ||
        !DERIVED_LOCAL.has(child.localName ?? "")
      ) {
        continue;
      }
      const refId = normText(child.textContent ?? "");
      const flow = flows.get(refId);
      const expected =
        child.localName === "incoming" ? flow?.tgt : flow?.src;
      if (!flow || expected !== elId) {
        diffs.push({
          kind: "REF_INCONSISTENCY",
          path: `${el.tagName}#${elId}`,
          detail: `${child.localName}="${refId}" não corresponde a endpoint de flow real`,
        });
      }
    }
  }
  return diffs;
}

export function compareBpmnXml(a: string, b: string): Diff[] {
  const ca = parseCanon(a);
  const cb = parseCanon(b);
  const diffs: Diff[] = [];
  compareEl(ca, cb, "/definitions", diffs);
  return diffs;
}

export function formatDiffs(diffs: Diff[]): string {
  return diffs
    .map((d) => `[${d.kind}] ${d.path} — ${d.detail}`)
    .join("\n");
}
