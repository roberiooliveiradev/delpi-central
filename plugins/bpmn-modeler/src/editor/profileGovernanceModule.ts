import VendorPaletteProvider from "bpmn-js/lib/features/palette/PaletteProvider";
import VendorContextPadProvider from "bpmn-js/lib/features/context-pad/ContextPadProvider";
import VendorReplaceMenuProvider from "bpmn-js/lib/features/popup-menu/ReplaceMenuProvider";

import {
  isClipboardElementAllowed,
  isContextPadEntryAllowed,
  isPaletteEntryAllowed,
  isReplaceEntryAllowed,
  isReplaceHeaderAllowed,
} from "./editingProfile";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Governança do editing profile da V1 sobre as surfaces vendor de criação.
 *
 * Extension point oficial: os service keys `paletteProvider`,
 * `contextPadProvider` e `replaceMenuProvider` são substituíveis via
 * additionalModules (último binding vence). Cada provider governado
 * instancia o provider vendor via `injector.instantiate` (que o
 * auto-registra na surface correspondente) e envolve o método público
 * com o filtro fail-closed da editingProfile central.
 *
 * Nenhum patch em node_modules, nenhum DOM scraping, nenhum CSS-hide:
 * a opção nunca é registrada no menu — não existe caminho para clicá-la.
 */

type Entries = Record<string, unknown>;

function filterEntries(entries: Entries, allowed: (key: string) => boolean): Entries {
  const kept: Entries = {};
  for (const key of Object.keys(entries || {})) {
    if (allowed(key)) kept[key] = entries[key];
  }
  return kept;
}

function GovernedPaletteProvider(this: any, injector: any) {
  const inner: any = injector.instantiate(VendorPaletteProvider);
  const original = inner.getPaletteEntries;
  inner.getPaletteEntries = function (...args: unknown[]) {
    return filterEntries(original.apply(this, args), isPaletteEntryAllowed);
  };
  return inner;
}

GovernedPaletteProvider.$inject = ["injector"];

function GovernedContextPadProvider(this: any, injector: any) {
  const inner: any = injector.instantiate(VendorContextPadProvider);
  const original = inner.getContextPadEntries;
  inner.getContextPadEntries = function (...args: unknown[]) {
    return filterEntries(
      original.apply(this, args),
      isContextPadEntryAllowed,
    );
  };
  return inner;
}

GovernedContextPadProvider.$inject = ["injector"];

function GovernedReplaceMenuProvider(this: any, injector: any) {
  const inner: any = injector.instantiate(VendorReplaceMenuProvider);
  const originalEntries = inner.getPopupMenuEntries;
  inner.getPopupMenuEntries = function (...args: unknown[]) {
    return filterEntries(
      originalEntries.apply(this, args),
      isReplaceEntryAllowed,
    );
  };
  const originalHeaders = inner.getPopupMenuHeaderEntries;
  inner.getPopupMenuHeaderEntries = function (...args: unknown[]) {
    return filterEntries(
      originalHeaders.apply(this, args),
      isReplaceHeaderAllowed,
    );
  };
  return inner;
}

GovernedReplaceMenuProvider.$inject = ["injector"];

/**
 * Governança do clipboard (G3) — paste/duplicate são paths de criação que
 * bypassam palette/context-pad/replace. Extension point oficial do vendor:
 * `copyPaste.canCopyElements` permite retornar o subconjunto copiável —
 * elementos preserve-only ficam de fora do clipboard tree (cut também não
 * os remove, pois o vendor só corta o que foi efetivamente copiado).
 */
function ProfileClipboardGovernance(this: any, eventBus: any) {
  eventBus.on("copyPaste.canCopyElements", (context: any) => {
    const elements = context?.elements ?? [];
    const allowed = elements.filter((el: any) =>
      isClipboardElementAllowed(el),
    );
    return allowed.length === elements.length ? undefined : allowed;
  });
}

ProfileClipboardGovernance.$inject = ["eventBus"];

export const profileGovernanceModule = {
  __init__: ["profileClipboardGovernance"],
  profileClipboardGovernance: ["type", ProfileClipboardGovernance],
  paletteProvider: ["type", GovernedPaletteProvider],
  contextPadProvider: ["type", GovernedContextPadProvider],
  replaceMenuProvider: ["type", GovernedReplaceMenuProvider],
};
