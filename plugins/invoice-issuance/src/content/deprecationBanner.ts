/** Copy de depreciação — soft cutover E12 (canônico = my-requests). */

export const DEPRECATION_BANNER = {
  testId: "deprecation-banner",
  message:
    "Este app legado está fora do menu. Use Minhas Solicitações para emissão de NF (URL direta ainda funciona até o desligamento completo).",
  primaryHref: "/apps/my-requests",
  primaryLabel: "Abrir Minhas Solicitações",
  createHref: "/apps/my-requests/new?type=invoice-issuance",
  createLabel: "Nova solicitação de NF",
} as const;
