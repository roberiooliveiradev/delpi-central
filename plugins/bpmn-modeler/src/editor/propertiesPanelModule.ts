import { Group } from "@bpmn-io/properties-panel";

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

export const propertiesPanelModule = {
  __init__: [
    "advancedIdProvider",
    "profileGovernedPanelProvider",
    "popupTitlePtBr",
    "textPopupProvider",
    "panelChromePtBr",
  ],
  advancedIdProvider: ["type", AdvancedIdProvider],
  profileGovernedPanelProvider: ["type", ProfileGovernedPanelProvider],
  popupTitlePtBr: ["type", PopupTitlePtBr],
  textPopupProvider: ["type", TextPopupProvider],
  panelChromePtBr: ["type", PanelChromePtBr],
};
