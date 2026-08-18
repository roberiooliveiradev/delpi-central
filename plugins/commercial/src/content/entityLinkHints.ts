/**
 * Textos PT de indicação de destino para links de entidade («Abrir…»).
 * Call sites usam os helpers — sem string solta.
 */

export const ENTITY_LINK_HINTS = {
  account: "Abrir conta de {name}",
  order: "Abrir pedido {order}",
  orderLine: "Abrir pedido {order}/{line}",
  openOrderLine: "Abrir detalhe do pedido {order}/{line}",
  opPage: "Abrir página da OP {op}",
  otdLine: "Abrir linha OTD {order}/{line}",
  invoice: "Abrir NF {invoice}",
  opportunity: "Abrir OV {ov}",
  proposal: "Abrir proposta {id}",
  profile: "Abrir perfil de {name}",
  portfolio: "Abrir carteira {label}",
  openOrdersFiltered: "Abrir Meus pedidos",
  product: "Abrir produto {code}",
  kpi: "Abrir indicador {label}",
} as const;

export type EntityLinkHintKey = keyof typeof ENTITY_LINK_HINTS;

function fillTemplate(
  template: string,
  vars: Record<string, string>,
): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => {
    const value = (vars[key] ?? "").trim();
    return value || "—";
  });
}

export function entityLinkTitle(
  key: EntityLinkHintKey,
  vars: Record<string, string> = {},
): string {
  return fillTemplate(ENTITY_LINK_HINTS[key], vars);
}

export function accountLinkTitle(name: string): string {
  return entityLinkTitle("account", { name: name.trim() || "cliente" });
}

export function profileLinkTitle(name: string): string {
  return entityLinkTitle("profile", { name: name.trim() || "usuário" });
}

export function opPageLinkTitle(op: string): string {
  return entityLinkTitle("opPage", { op: op.trim() || "—" });
}

export function orderLinkTitle(order: string, line?: string): string {
  const o = order.trim() || "—";
  const l = (line ?? "").trim();
  if (l) return entityLinkTitle("orderLine", { order: o, line: l });
  return entityLinkTitle("order", { order: o });
}

export function openOrderLineLinkTitle(order: string, line: string): string {
  return entityLinkTitle("openOrderLine", {
    order: order.trim() || "—",
    line: line.trim() || "—",
  });
}

export function otdLineLinkTitle(order: string, line: string): string {
  return entityLinkTitle("otdLine", {
    order: order.trim() || "—",
    line: line.trim() || "—",
  });
}

export function invoiceLinkTitle(invoice: string): string {
  return entityLinkTitle("invoice", { invoice: invoice.trim() || "—" });
}

export function opportunityLinkTitle(ov: string): string {
  return entityLinkTitle("opportunity", { ov: ov.trim() || "—" });
}

export function proposalLinkTitle(id: string): string {
  return entityLinkTitle("proposal", { id: id.trim() || "—" });
}

export function portfolioLinkTitle(label: string): string {
  return entityLinkTitle("portfolio", { label: label.trim() || "—" });
}

export function productLinkTitle(code: string): string {
  return entityLinkTitle("product", { code: code.trim() || "—" });
}

export function kpiLinkTitle(label: string): string {
  return entityLinkTitle("kpi", { label: label.trim() || "indicador" });
}
