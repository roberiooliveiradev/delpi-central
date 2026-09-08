/** Mensagens HTTP amigáveis do Portal Suprimentos (sem HTML de gateway). */
export const HTTP_ERROR_CONTENT = {
  gatewayUnavailable:
    "O Portal Suprimentos está temporariamente indisponível. Tente novamente em instantes.",
  httpFallback: (status: number) => `Erro HTTP ${status}`,
} as const;
