/** Mensagens HTTP amigáveis do Portal Comercial (sem corpo HTML de gateway). */
export const HTTP_ERROR_CONTENT = {
  gatewayUnavailable:
    "O serviço comercial está temporariamente indisponível. Tente novamente em instantes.",
  httpFallback: (status: number) => `Erro HTTP ${status}`,
} as const;
