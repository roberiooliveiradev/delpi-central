/** Deep link para a bancada de pedidos em aberto do Portal Comercial. */
export function buildCommercialOpenOrderPath(options: {
  pedido: string;
  linha?: string | null;
  filial?: string | null;
}): string | null {
  const pedido = String(options.pedido || "").trim();
  if (!pedido) return null;
  const params = new URLSearchParams();
  params.set("pedido", pedido);
  const linha = String(options.linha || "").trim();
  if (linha) params.set("linha", linha);
  const filial = String(options.filial || "").trim();
  if (filial) params.set("filial", filial);
  return `/apps/commercial/open-orders?${params.toString()}`;
}
