import {
  buildAnalyticsOpportunityDetailPath,
  buildAnalyticsOtdLinePath,
  buildCustomerDetailPath,
  buildCustomerInvoiceDetailPath,
  buildCustomerOrderDetailPath,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildPluginPath,
  buildProposalDetailPath,
  buildSellerPortfolioDetailPath,
  buildUserProfilePath,
} from "../../app/pluginRoutes";

function refStr(ref: Record<string, unknown>, ...keys: string[]): string {
  for (const key of keys) {
    const value = String(ref[key] ?? "").trim();
    if (value) return value;
  }
  return "";
}

/**
 * hrefStrategy do catálogo de menções → path EN do MFE Comercial.
 * Retorna null quando faltam chaves (card sem botão Abrir).
 */
export function resolveInteractionEntityHref(
  basePath: string,
  hrefStrategy: string,
  ref: Record<string, unknown>,
): string | null {
  const strategy = hrefStrategy.trim();
  switch (strategy) {
    case "user_profile": {
      const userId = refStr(ref, "user_id", "id");
      return buildUserProfilePath(basePath, userId);
    }
    case "customer_detail": {
      const code = refStr(ref, "customer_code", "code");
      const store = refStr(ref, "customer_store", "store");
      return buildCustomerDetailPath(basePath, code, store);
    }
    case "portfolio_detail": {
      const portfolioId = refStr(ref, "portfolio_id", "id");
      return buildSellerPortfolioDetailPath(basePath, portfolioId);
    }
    case "order_detail": {
      const branch = refStr(ref, "branch", "filial");
      const order = refStr(ref, "order", "pedido");
      const code = refStr(ref, "customer_code", "codigo");
      const store = refStr(ref, "customer_store", "loja");
      if (code && store && branch && order) {
        return buildCustomerOrderDetailPath(basePath, code, store, branch, order);
      }
      const line = refStr(ref, "line", "linha", "line_item") || "001";
      if (branch && order) {
        return buildOpenOrderLineDetailPath(basePath, branch, order, line);
      }
      return null;
    }
    case "production_order_detail": {
      const branch = refStr(ref, "branch", "filial");
      const order = refStr(ref, "order", "pedido");
      const line = refStr(ref, "line", "linha", "line_item");
      const op = refStr(ref, "production_order", "op");
      if (branch && order && line && op) {
        return buildOpenOrderOpDetailPath(basePath, branch, order, line, op);
      }
      return null;
    }
    case "opportunity_detail": {
      const number = refStr(ref, "proposal_number", "opportunity_id", "id");
      return buildAnalyticsOpportunityDetailPath(basePath, number);
    }
    case "proposal_detail": {
      const id = refStr(ref, "proposal_id", "id");
      return buildProposalDetailPath(basePath, id);
    }
    case "otd_line": {
      const branch = refStr(ref, "branch", "filial");
      const order = refStr(ref, "order", "pedido");
      const line = refStr(ref, "line", "linha", "line_item");
      return buildAnalyticsOtdLinePath(basePath, branch, order, line);
    }
    case "invoice_detail": {
      const code = refStr(ref, "customer_code", "codigo");
      const store = refStr(ref, "customer_store", "loja");
      const branch = refStr(ref, "branch", "filial");
      const doc = refStr(ref, "invoice", "documento", "doc", "invoice_number");
      const series = refStr(ref, "series", "invoice_series", "serie");
      return buildCustomerInvoiceDetailPath(
        basePath,
        code,
        store,
        branch,
        doc,
        series,
      );
    }
    case "product_factory": {
      return buildPluginPath("home", basePath);
    }
    case "my_day": {
      return buildPluginPath("my_tasks", basePath);
    }
    default:
      return null;
  }
}

export function parseRoomEntityKey(
  entityKey: string | null | undefined,
): [string, string] | null {
  const raw = (entityKey ?? "").trim();
  const sep = raw.indexOf("|");
  if (sep <= 0) return null;
  const left = raw.slice(0, sep).trim();
  const right = raw.slice(sep + 1).trim();
  if (!left || !right) return null;
  return [left, right];
}

/** `entity_type` + `entity_key` da sala → path do MFE (fail-open). */
export function resolveRoomEntityHref(
  basePath: string,
  entityType?: string | null,
  entityKey?: string | null,
): string | null {
  const kind = (entityType ?? "").trim().toLowerCase();
  const parsed = parseRoomEntityKey(entityKey);
  if (!parsed) return null;
  const [left, right] = parsed;
  if (kind === "customer") {
    return resolveInteractionEntityHref(basePath, "customer_detail", {
      customer_code: left,
      customer_store: right,
    });
  }
  if (kind === "order") {
    return resolveInteractionEntityHref(basePath, "order_detail", {
      branch: left,
      order: right,
    });
  }
  if (kind === "production_order") {
    return resolveInteractionEntityHref(basePath, "production_order_detail", {
      branch: left,
      production_order: right,
    });
  }
  return null;
}
