import { Group } from "@bpmn-io/properties-panel";

import { bpmnTypeLabel } from "./i18n/translate";

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
  eventBus.on("propertiesPanel.openPopup", 1500, (event: any) => {
    const element = event?.element;
    if (!element?.type || typeof element.type !== "string") return;
    event.element = { ...element, type: bpmnTypeLabel(element.type) };
  });
}

PopupTitlePtBr.$inject = ["eventBus"];

export const propertiesPanelModule = {
  __init__: ["advancedIdProvider", "popupTitlePtBr"],
  advancedIdProvider: ["type", AdvancedIdProvider],
  popupTitlePtBr: ["type", PopupTitlePtBr],
};
