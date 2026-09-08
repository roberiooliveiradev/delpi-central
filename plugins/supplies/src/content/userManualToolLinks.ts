/**
 * Destinos citáveis no Manual → rotas do Portal Suprimentos.
 * Labels mais longos primeiro (match guloso no texto).
 */
import type { PluginNavigationTarget } from "../app/pluginRoutes";

export type ManualToolTarget = {
  label: string;
  viewId: PluginNavigationTarget;
  search?: string;
};

export const MANUAL_TOOL_TARGETS: readonly ManualToolTarget[] = [
  { label: "Estoque de segurança", viewId: "safety_stock" },
  { label: "Solicitações de compras", viewId: "purchase_requests" },
  { label: "Pedidos de compra", viewId: "purchase_orders" },
  { label: "Minhas tarefas", viewId: "my_tasks" },
  { label: "Visão geral", viewId: "overview" },
  { label: "Administração", viewId: "administration" },
  { label: "Fornecedores", viewId: "suppliers" },
  { label: "Indicadores", viewId: "indicators" },
  { label: "Produtos", viewId: "products" },
  { label: "Entregas", viewId: "deliveries" },
  { label: "Estoque", viewId: "inventory" },
  { label: "Início", viewId: "home" },
  { label: "Ajuda", viewId: "help" },
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
