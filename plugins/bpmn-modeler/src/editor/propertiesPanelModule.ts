import { Group } from "@bpmn-io/properties-panel";

import { bpmnTypeLabel, translate } from "./i18n/translate";

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
 * Chrome interno do painel (launcher "Open pop-up editor", placeholder
 * "Opened in editor", títulos de toggle/section): bpmn-js-properties-panel
 * 5.65.1 resolve `translate` via useService nos providers, mas NÃO repassa
 * a prop `translate` aos leaf entries (@bpmn-io/properties-panel usa
 * `translateFallback` quando a prop não chega). Não existe extension point
 * para esses strings — JUSTIFIED_VENDOR_OVERRIDE:
 *
 * Um passe único e delimitado após `propertiesPanel.rendered`/`openPopup`
 * traduz title/textContent APENAS quando o valor é exatamente um template
 * EN conhecido do dicionário PT-BR (lookup retorna diferente do input).
 * Sem MutationObserver, sem seletores genéricos de texto, escopo restrito
 * ao container do painel.
 */
function PanelChromePtBr(this: any, eventBus: any, propertiesPanel: any) {
  const fix = () => {
    const root = propertiesPanel?._container as HTMLElement | undefined;
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
          ".bio-properties-panel-feel-editor__open-popup-placeholder",
      ),
    )) {
      const pt = translate(el.textContent ?? "");
      if (el.textContent !== pt) el.textContent = pt;
    }
  };
  eventBus.on("propertiesPanel.rendered", fix);
  eventBus.on("propertiesPanel.updated", fix);
  // o placeholder "Opened in editor" aparece quando o popup abre —
  // o fire chega antes do re-render; agenda para depois do commit DOM.
  const deferred = () => {
    setTimeout(fix, 0);
    requestAnimationFrame(fix);
  };
  eventBus.on("propertiesPanel.openPopup", deferred);
  eventBus.on("propertiesPanelPopup.open", deferred);
  eventBus.on("propertiesPanelPopup.close", deferred);
}

PanelChromePtBr.$inject = ["eventBus", "propertiesPanel"];

export const propertiesPanelModule = {
  __init__: ["advancedIdProvider", "popupTitlePtBr", "panelChromePtBr"],
  advancedIdProvider: ["type", AdvancedIdProvider],
  popupTitlePtBr: ["type", PopupTitlePtBr],
  panelChromePtBr: ["type", PanelChromePtBr],
};
