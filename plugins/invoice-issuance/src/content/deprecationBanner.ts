/** Copy de depreciação — dual-run E8 (canônico = my-requests). */

export const DEPRECATION_BANNER = {
  testId: "deprecation-banner",
  message:
    "Este app legado permanece em dual-run. O fluxo canônico de emissão de NF é Minhas Solicitações.",
  primaryHref: "/apps/my-requests",
  primaryLabel: "Abrir Minhas Solicitações",
  createHref: "/apps/my-requests/new?type=invoice-issuance",
  createLabel: "Nova solicitação de NF",
} as const;
