/**
 * Destinos citáveis no Manual do usuário → rotas do Portal.
 * Labels mais longos primeiro (match guloso no texto).
 */
import type { PluginNavigationTarget } from "../app/pluginRoutes";

export type ManualToolTarget = {
  label: string;
  viewId: PluginNavigationTarget;
  search?: string;
};

export const MANUAL_TOOL_TARGETS: readonly ManualToolTarget[] = [
  { label: "Pontualidade (OTD)", viewId: "analytics_otd" },
  { label: "Sala de interação", viewId: "interaction_rooms" },
  { label: "Manual do usuário", viewId: "help" },
  { label: "Minha Carteira → Faturamento", viewId: "customers", search: "?panel=billing" },
  { label: "Minha Carteira → ABC", viewId: "customers", search: "?panel=abc" },
  { label: "Minha Carteira", viewId: "customers" },
  { label: "Minhas tarefas", viewId: "my_tasks" },
  { label: "Meus pedidos", viewId: "open_orders" },
  { label: "Visão geral", viewId: "overview" },
  { label: "Administração", viewId: "administration" },
  { label: "Oportunidades", viewId: "analytics_opportunities" },
  { label: "Propostas", viewId: "proposals" },
  { label: "Início", viewId: "home" },
  { label: "Ajuda", viewId: "help" },
  { label: "OTD", viewId: "analytics_otd" },
] as const;

export type ManualTextPart =
  | { kind: "text"; value: string }
  | {
      kind: "link";
      value: string;
      viewId: PluginNavigationTarget;
      search?: string;
    };

/** Quebra o texto intercalando links nas ferramentas citadas (labels exatos). */
export function splitManualTextWithToolLinks(text: string): ManualTextPart[] {
  if (!text) return [];
  const parts: ManualTextPart[] = [];
  let remaining = text;

  while (remaining.length > 0) {
    let earliest = -1;
    let matched: ManualToolTarget | null = null;

    for (const target of MANUAL_TOOL_TARGETS) {
      const idx = remaining.indexOf(target.label);
      if (idx < 0) continue;
      if (
        earliest < 0 ||
        idx < earliest ||
        (idx === earliest &&
          matched !== null &&
          target.label.length > matched.label.length)
      ) {
        earliest = idx;
        matched = target;
      }
    }

    if (earliest < 0 || !matched) {
      parts.push({ kind: "text", value: remaining });
      break;
    }

    if (earliest > 0) {
      parts.push({ kind: "text", value: remaining.slice(0, earliest) });
    }
    parts.push({
      kind: "link",
      value: matched.label,
      viewId: matched.viewId,
      search: matched.search,
    });
    remaining = remaining.slice(earliest + matched.label.length);
  }

  return parts;
}
