/**
 * Preservação de extensões BPMN desconhecidas no path editor
 * (G4-EXT-1 — root cause: bpmn-moddle@10.3.1 + moddle-xml).
 *
 * Duas perdas provadas no vendor:
 *
 * A) `bpmn:extension/@definition` — o descriptor declara a prop como
 *    `isReference` para `ExtensionDefinition`; o valor QName (`vend:suite`)
 *    não resolve para um id de elemento → dropada no PARSE. Reparo:
 *    `repairExtensionDeclarations` instala uma referência léxica
 *    `{ id: "vend:suite" }` — o serializer emite isReference como `.id`,
 *    reemitindo o QName textual intacto. É suporte de parser/serializer,
 *    não ownership de domínio: o XML BPMN continua a única fonte canônica.
 *
 * B) attr namespaced `{ns}x` em elemento `{ns}e` (mesma URI) dentro de
 *    `extensionElements` — `ElementSerializer.nsAttributeName` stripa o
 *    prefixo quando a URI do attr === URI do elemento (`isLocalNs`).
 *    Isso é incorreto em XML (attrs nunca herdam o default ns) e NÃO é
 *    corrigível por descriptor nem por estado do modelo — o serializer
 *    simplesmente não consegue emitir esse formato. Política: fail-closed
 *    → `hasUnpreservableExtensionContent` detecta → read-only + save
 *    blocked; o artefato canônico permanece byte-exact.
 */
const BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL";

type ModdleDescriptor = {
  properties?: Array<{ name: string; isReference?: boolean }>;
};

type ModdleExtension = {
  $attrs?: Record<string, unknown>;
  $descriptor?: ModdleDescriptor;
  [key: string]: unknown;
};

type ModdleDefinitions = {
  extensions?: ModdleExtension[];
};

/**
 * Copia para o modelo os attrs de `<bpmn:extension>` que o descriptor
 * vendor descartou no parse (hoje: `definition` — isReference para
 * `bpmn:ExtensionDefinition` não resolvível, pois o valor é um QName
 * léxico, não o id de um elemento do documento).
 *
 * O serializer moddle-xml emite props `isReference` como `value.id`, então
 * o reparo usa um objeto de referência léxica `{ id: "<qname textual>" }`
 * — suporte de serializer, não ownership de domínio. Attrs não declarados
 * no descriptor já chegam ao modelo via `$attrs` (canal genérico) e são
 * reemitidos intactos; o fallback `$attrs` cobre qualquer outro attr
 * declarado que venha a ser dropado.
 *
 * Ordem do array `definitions.extensions` == ordem do documento; o DOM
 * bruto é a fonte de verdade, o modelo só recebe o delta.
 */
export function repairExtensionDeclarations(
  definitions: ModdleDefinitions,
  xml: string,
): void {
  const extensions = definitions.extensions;
  if (!extensions?.length) return;
  try {
    const doc = new DOMParser().parseFromString(xml, "application/xml");
    const raw = Array.from(doc.getElementsByTagNameNS(BPMN_NS, "extension"));
    const n = Math.min(extensions.length, raw.length);
    for (let i = 0; i < n; i += 1) {
      const ext = extensions[i];
      const props = ext.$descriptor?.properties;
      for (const attr of Array.from(raw[i].attributes)) {
        if (attr.prefix === "xmlns" || attr.name === "xmlns") continue;
        const has =
          ext[attr.name] !== undefined ||
          ext.$attrs?.[attr.name] !== undefined;
        if (has) continue;
        const prop = props?.find((p) => p.name === attr.name);
        if (prop?.isReference) {
          ext[attr.name] = { id: attr.value };
        } else {
          ext.$attrs = { ...(ext.$attrs ?? {}), [attr.name]: attr.value };
        }
      }
    }
  } catch {
    // reparo best-effort: falha de DOM parse não pode quebrar o import
  }
}

/**
 * Detecta conteúdo de extensão que o serializer vendor provadamente não
 * consegue emitir: attr com prefixo cuja URI === URI do elemento que o
 * contém (moddle-xml `isLocalNs` stripa o prefixo → perda de namespace).
 * Também cobre prefixo não resolvível (attr serializável seria dropado).
 * Análise estruturada via DOM — nunca regex/string sobre o XML.
 */
export function hasUnpreservableExtensionContent(xml: string): boolean {
  try {
    const doc = new DOMParser().parseFromString(xml, "application/xml");
    for (const el of Array.from(doc.querySelectorAll("*"))) {
      for (const attr of Array.from(el.attributes)) {
        const prefix = attr.prefix;
        if (!prefix || prefix === "xmlns" || prefix === "xml") continue;
        const attrUri = el.lookupNamespaceURI(prefix);
        if (attrUri === null || attrUri === el.namespaceURI) {
          return true;
        }
      }
    }
  } catch {
    return false;
  }
  return false;
}
