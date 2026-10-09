import {
  CheckboxEntry,
  Group,
  TextFieldEntry,
  isCheckboxEntryEdited,
  isTextFieldEntryEdited,
} from "@bpmn-io/properties-panel";
// NOTE: os leaf entries do painel normalmente resolvem serviços via hook
// `useService` do bundle vendor — ele puxa o bpmn-js inteiro na importação.
// O BpmnCorePropsProvider resolve os mesmos serviços direto do `injector`
// (didi) e passa por closure: mesmo contrato, boundary explícito, testável.

import { bpmnTypeLabel, translate } from "./i18n/translate";
import {
  isPropertiesEntryAllowed,
  isPropertiesGroupAllowed,
} from "./editingProfile";
import { TextPopupPtBr } from "./popups/textPopup";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Provider de baixa prioridade do properties panel: move o entry técnico
 * `id` do grupo "Geral" para um grupo colapsável "Configurações avançadas".
 *
 * Extension point oficial (`propertiesPanel.registerProvider` +
 * `getGroups` chain) — o entry continua sendo o componente vendor, com o
 * mesmo binding/command stack/validação. Nenhum DOM é movido.
 */
function AdvancedIdProvider(this: any, propertiesPanel: any, translate: any) {
  // prioridade abaixo dos providers built-in → o mutator roda por último,
  // depois que os grupos vendor já foram montados.
  propertiesPanel.registerProvider(1, this);
  this._translate = translate;
}

AdvancedIdProvider.$inject = ["propertiesPanel", "translate"];

const TECHNICAL_ENTRY_IDS = new Set(["id", "processId"]);

AdvancedIdProvider.prototype.getGroups = function () {
  const translate = this._translate;
  return (groups: any[]) => {
    const moved: any[] = [];
    for (const group of groups) {
      if (!Array.isArray(group?.entries)) continue;
      for (let i = group.entries.length - 1; i >= 0; i--) {
        if (TECHNICAL_ENTRY_IDS.has(group.entries[i]?.id)) {
          moved.unshift(...group.entries.splice(i, 1));
        }
      }
    }

    // hierarquia do produto: "Geral" (Nome/Executável) abre por padrão;
    // "Configurações avançadas" permanece recolhido
    const general = groups.find((g) => g?.id === "general");
    if (general) general.shouldOpen = true;

    if (!moved.length) return groups;

    // grupo que ficou vazio após a remoção do id é descartado
    const kept = groups.filter(
      (g) => g === null || !Array.isArray(g.entries) || g.entries.length > 0,
    );

    const advanced = kept.find((g) => g?.id === "advanced");
    if (advanced) {
      advanced.entries.push(...moved);
      return kept;
    }

    kept.push({
      id: "advanced",
      label: translate("Advanced settings"),
      tooltip: translate(
        "Technical settings stored in the BPMN file. Changes may affect external references and integrations.",
      ),
      component: Group,
      entries: moved,
    });
    return kept;
  };
};

/**
 * Título do popup de campo expandido ("editor ampliado"): o vendor monta
 * `${element.type} / ${label}` com o tipo moddle cru (`bpmn:Process`).
 * O evento `propertiesPanel.openPopup` (extension point do eventBus) chega
 * antes do popup manager — troca `element` por um clone com o type label
 * PT-BR. O elemento real nunca é mutado.
 */
function PopupTitlePtBr(this: any, eventBus: any) {
  eventBus.on(
    "propertiesPanel.openPopup",
    1500,
    (event: any, context: any) => {
      // o event copia o context (InternalEvent.init → assign): o Popup
      // lê `context.element` no segundo arg — mutar ambos para o título
      // chegar ao getPopupTitle do vendor como "Evento inicial / Nome".
      const element = context?.element ?? event?.element;
      if (!element?.type || typeof element.type !== "string") return;
      const clone = { ...element, type: bpmnTypeLabel(element.type) };
      if (context) context.element = clone;
      event.element = clone;
    },
  );
}

PopupTitlePtBr.$inject = ["eventBus"];

/**
 * Provider de popup "text" (editor ampliado de textarea): recria o
 * TextPopup do vendor via componentes exportados (Popup/Popup.Title/
 * Popup.Body) e traduz o `closeButtonTooltip`, que o vendor hardcoda
 * como "Save and close" sem prop de tradução.
 * Extension point oficial: `feelPopup.registerProvider('text', ...)`.
 */
function TextPopupProvider(this: any, feelPopup: any, translate: any) {
  feelPopup.registerProvider("text", (props: any) =>
    TextPopupPtBr({ ...props, translate }),
  );
}

TextPopupProvider.$inject = ["feelPopup", "translate"];

/**
 * JUSTIFIED_VENDOR_WORKAROUND — chrome residual não traduzível.
 *
 * Gap provado no vendor instalado (bpmn-js-properties-panel@5.65.1 +
 * @bpmn-io/properties-panel@3.55.0): os componentes intermediários
 * (ex.: `ElementDocumentationProperty`) resolvem `translate` via
 * `useService`, mas chamam os leaf entries (`TextAreaEntry` etc.) como
 * função com lista fixa de props — `translate` nunca é repassado e o
 * leaf cai em `translateFallback`. O `{...entry}` spread do renderer
 * não ajuda: o descriptor recebe a prop, mas o intermediário a ignora.
 *
 * Strings afetadas (todas hardcoded no leaf, sem extension point):
 *   - launcher `title="Open pop-up editor"` (OpenPopupButton);
 *   - placeholder "Opened in editor" (TextAreaEntry/FeelEntry);
 *   - tooltip "Save and close" do FeelPopup (não exportado — não dá
 *     para re-renderizá-lo como fazemos com o TextPopup).
 *
 * Delimitação do workaround:
 *   - só roda em eventos oficiais do vendor (rendered/updated/
 *     popup open-close/feelPopup.opened);
 *   - escopo = `propertiesPanel._container` ou o `domNode` entregue
 *     pelo evento — nenhum seletor global, nenhum MutationObserver,
 *     nenhum polling;
 *   - só reescreve `title`/`textContent` cujo valor é exatamente um
 *     template EN conhecido do dicionário (lookup ≠ input);
 *   - `queueMicrotask` (não setTimeout/interval): o commit do preact
 *     é microtask — agendar depois dele é ordenado e único, não polling.
 *
 * Remover quando o vendor propagar `translate` aos leafs ou expor
 * config/prop para essas strings.
 */
function PanelChromePtBr(this: any, eventBus: any, propertiesPanel: any) {
  const fix = (root?: HTMLElement | null) => {
    if (!root) return;
    for (const el of Array.from(
      root.querySelectorAll<HTMLElement>("[title]"),
    )) {
      const title = el.getAttribute("title") ?? "";
      const pt = translate(title);
      if (pt !== title) el.setAttribute("title", pt);
    }
    for (const el of Array.from(
      root.querySelectorAll<HTMLElement>(
        ".bio-properties-panel-textarea__open-popup-placeholder, " +
          ".bio-properties-panel-feel-editor__open-popup-placeholder, " +
          ".bio-properties-panel-feelers-editor__popup-placeholder",
      ),
    )) {
      const pt = translate(el.textContent ?? "");
      if (el.textContent !== pt) el.textContent = pt;
    }
  };

  const container = () => propertiesPanel?._container as HTMLElement | null;
  // commit síncrono do render do vendor
  eventBus.on("propertiesPanel.rendered", () => fix(container()));
  // updated/openPopup disparam ANTES do commit interno (microtask do
  // preact) — agenda o fix para depois dele, uma única vez por evento
  const deferred = () => queueMicrotask(() => fix(container()));
  eventBus.on("propertiesPanel.updated", deferred);
  eventBus.on("propertiesPanelPopup.open", deferred);
  eventBus.on("propertiesPanelPopup.close", deferred);
  // popup FEEL renderiza fora do container do painel: o evento oficial
  // entrega o próprio domNode já commitado (render() do preact é
  // síncrono) — fix direto. O field in-panel re-renderiza com o
  // placeholder "Opened in editor" num listener do vendor cuja ordem
  // de commit não é garantida: rAF single-shot é a única fronteira
  // determinística pós-commit (frame boundary, não polling nem timer);
  // microtask é o fallback para ambientes sem rAF (testes node).
  const afterCommit =
    typeof requestAnimationFrame === "function"
      ? requestAnimationFrame
      : (f: () => void) => queueMicrotask(f);
  eventBus.on("feelPopup.opened", (context: any) => {
    fix(context?.domNode as HTMLElement | undefined);
    afterCommit(() => fix(container()));
  });
  eventBus.on("feelPopup.closed", () => afterCommit(() => fix(container())));
}

PanelChromePtBr.$inject = ["eventBus", "propertiesPanel"];

/**
 * Provider de governança do editing profile (G2A): remove grupos e entries
 * fora do profile aprovado da V1 (multiInstance, adHocCompletion,
 * compensation; entry isExecutable — atributo BPMN normativo cuja edição
 * é intencionalmente não exposta, ver editingProfile.ts). Extension point
 * oficial `registerProvider`
 * na mesma prioridade do AdvancedIdProvider — mutação de lista de grupos,
 * nenhum DOM manipulado. Fail-closed: grupo ou entry vendor
 * novo/desconhecido cai em deny (ver editingProfile.ts).
 */
function ProfileGovernedPanelProvider(this: any, propertiesPanel: any) {
  propertiesPanel.registerProvider(1, this);
}

ProfileGovernedPanelProvider.$inject = ["propertiesPanel"];

ProfileGovernedPanelProvider.prototype.getGroups = function () {
  return (groups: any[]) => {
    const kept = groups.filter(
      (g) => g === null || isPropertiesGroupAllowed(g?.id),
    );
    for (const group of kept) {
      if (!Array.isArray(group?.entries)) continue;
      group.entries = group.entries.filter((e: any) =>
        isPropertiesEntryAllowed(e?.id),
      );
    }
    return kept;
  };
};

// ---------------------------------------------------------------------------
// BPMN core properties ausentes da surface `bpmn` vendor (Wave E)
// ---------------------------------------------------------------------------
//
// `calledElement` (CallActivity), `conditionExpression` (SequenceFlow) e
// `default` (SequenceFlow via source) são BPMN 2.0 CORE normativo — o
// provider genérico `bpmn` não os emite (o código equivalente vive nos
// providers zeebe/camunda-platform, que não são autoridade do produto e
// carregam semântica de engine). Implementados aqui via mesma extension
// point (`propertiesPanel.registerProvider` + concat de grupos), entries
// leaf do vendor e command stack (`modeling.updateProperties` /
// `modeling.updateModdleProperties`) — nenhuma mutação direta de
// businessObject, nenhuma semantic de engine (binding/version/etc.).
//
// Contextos válidos (BPMN spec + mesmo conjunto do vendor
// CONDITIONAL_SOURCES): condition/default só existem em SequenceFlow cujo
// source é Activity, ExclusiveGateway ou InclusiveGateway. Exclusão
// mútua normativa: flow com conditionExpression não pode ser default (a
// UI nunca expõe os dois campos simultaneamente).

const FLOW_SEMANTIC_SOURCES = [
  "bpmn:Activity",
  "bpmn:ExclusiveGateway",
  "bpmn:InclusiveGateway",
];

// helpers moddle locais — equivalentes a `is`/`isAny`/`getBusinessObject`
// do vendor sem importar módulos internos do bpmn-js (mantém o provider
// testável no vitest e o boundary vendor explícito).
const boOf = (element: any): any => element?.businessObject ?? element;

function boIs(element: any, type: string): boolean {
  const bo = boOf(element);
  if (!bo) return false;
  if (typeof bo.$instanceOf === "function") return bo.$instanceOf(type);
  return bo.$type === type;
}

function isFlowSemanticSource(element: any): boolean {
  return FLOW_SEMANTIC_SOURCES.some((t) => boIs(element, t));
}

/** calledElement — BPMN core `bpmn:CallActivity@calledElement` (QName). */
function calledElementField(injector: any) {
  return function CalledElementField(props: any) {
    const { element } = props;
    const modeling = injector.get("modeling");
    const debounce = injector.get("debounceInput");
    const t = injector.get("translate");
  return TextFieldEntry({
    element,
    id: "calledElement",
    label: t("Called element"),
    getValue: () =>
      boOf(element).get("calledElement") ?? "",
    setValue: (value: string) =>
      modeling.updateProperties(element, {
        calledElement: value?.trim() || null,
      }),
    debounce,
  });
};
}

/**
 * conditionExpression — `bpmn:SequenceFlow.conditionExpression` é child
 * `bpmn:Expression` serializado via xsi:type; criamos
 * `bpmn:FormalExpression` (superType da Expression) com `body`.
 * Clear = moddle property null → remove o child element.
 */
function conditionExpressionField(injector: any) {
  return function ConditionExpressionField(props: any) {
    const { element } = props;
    const modeling = injector.get("modeling");
    const bpmnFactory = injector.get("bpmnFactory");
    const debounce = injector.get("debounceInput");
    const t = injector.get("translate");
    const bo = boOf(element);
    return TextFieldEntry({
      element,
      id: "conditionExpression",
      label: t("Condition expression"),
    getValue: () => bo.get("conditionExpression")?.get("body") ?? "",
    setValue: (value: string) => {
      const body = value?.trim() ?? "";
      const existing = bo.get("conditionExpression");
      if (!body) {
        if (existing) {
          modeling.updateModdleProperties(element, bo, {
            conditionExpression: null,
          });
        }
        return;
      }
      if (existing) {
        modeling.updateModdleProperties(element, existing, { body });
        return;
      }
      const expression = bpmnFactory.create("bpmn:FormalExpression", {
        body,
      });
      expression.$parent = bo;
      modeling.updateModdleProperties(element, bo, {
        conditionExpression: expression,
      });
    },
    debounce,
    });
  };
}

/**
 * default — `bpmn:Activity|ExclusiveGateway|InclusiveGateway@default` é
 * IDREF para uma SequenceFlow outgoing. Toggle ON escreve no SOURCE
 * (`default = este flow`, exclusivo por construção do atributo); OFF só
 * limpa se este flow for o default atual.
 */
function defaultFlowField(injector: any) {
  return function DefaultFlowField(props: any) {
    const { element } = props;
    const modeling = injector.get("modeling");
    const t = injector.get("translate");
    const bo = boOf(element);
    const source = element.source;
    const sourceBo = source && boOf(source);
    const isDefault = () => !!sourceBo && sourceBo.get("default") === bo;
    return CheckboxEntry({
      element,
      id: "defaultFlow",
      label: t("Default Flow"),
      getValue: isDefault,
      setValue: (checked: boolean) => {
        if (checked) {
          modeling.updateProperties(source, { default: bo });
        } else if (isDefault()) {
          modeling.updateProperties(source, { default: null });
        }
      },
    });
  };
}

function flowCoreEntries(element: any, injector: any): any[] {
  const bo = boOf(element);
  const source = element.source;
  if (!isFlowSemanticSource(source)) return [];
  const isDefault = !!source && boOf(source).get("default") === bo;
  const hasCondition = !!bo.get("conditionExpression");
  const entries: any[] = [];
  // exclusão mútua: default flow não carrega condition (BPMN); flow com
  // condition não pode virar default enquanto a condition existir.
  if (!isDefault) {
    entries.push({
      id: "conditionExpression",
      component: conditionExpressionField(injector),
      isEdited: isTextFieldEntryEdited,
    });
  }
  if (!hasCondition) {
    entries.push({
      id: "defaultFlow",
      component: defaultFlowField(injector),
      isEdited: isCheckboxEntryEdited,
    });
  }
  return entries;
}

function BpmnCorePropsProvider(this: any, propertiesPanel: any, injector: any) {
  propertiesPanel.registerProvider(this);
  this._injector = injector;
}

BpmnCorePropsProvider.$inject = ["propertiesPanel", "injector"];

BpmnCorePropsProvider.prototype.getGroups = function (element: any) {
  const injector = this._injector;
  return (groups: any[]) => {
    const extras: any[] = [];

    if (boIs(element, "bpmn:CallActivity")) {
      extras.push({
        id: "callActivity",
        label: translate("Call Activity"),
        component: Group,
        entries: [
          {
            id: "calledElement",
            component: calledElementField(injector),
            isEdited: isTextFieldEntryEdited,
          },
        ],
      });
    }

    if (boIs(element, "bpmn:SequenceFlow")) {
      const entries = flowCoreEntries(element, injector);
      if (entries.length) {
        extras.push({
          id: "flow",
          label: translate("Sequence Flow"),
          component: Group,
          entries,
        });
      }
    }

    return extras.length ? groups.concat(extras) : groups;
  };
};

export const propertiesPanelModule = {
  __init__: [
    "advancedIdProvider",
    "profileGovernedPanelProvider",
    "bpmnCorePropsProvider",
    "popupTitlePtBr",
    "textPopupProvider",
    "panelChromePtBr",
  ],
  advancedIdProvider: ["type", AdvancedIdProvider],
  profileGovernedPanelProvider: ["type", ProfileGovernedPanelProvider],
  bpmnCorePropsProvider: ["type", BpmnCorePropsProvider],
  popupTitlePtBr: ["type", PopupTitlePtBr],
  textPopupProvider: ["type", TextPopupProvider],
  panelChromePtBr: ["type", PanelChromePtBr],
};
