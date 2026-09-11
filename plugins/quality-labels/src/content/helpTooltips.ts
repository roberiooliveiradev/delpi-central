/**
 * Ajuda in-app das Etiquetas da Qualidade.
 * Fonte canônica dos textos visíveis ao inspetor — não duplicar copy nas páginas.
 */
export const QL_HELP_TOOLTIPS = {
  overview: {
    etiquetaVsQr:
      "A etiqueta física mostra o rótulo CLIENTE e a referência do cadastro (B1_REFEREN). Nome do cliente e código do desenho (B1_CODDES) aparecem ao ler o QR e nos metadados de auditoria.",
  },
  labels: {
    print:
      "Imprime a etiqueta 100×30 mm: na frente, QR + CLIENTE + referência; no verso, marca Delpi, selo e código do produto. Nome e desenho não cabem na mídia — ficam no QR.",
    publicPage:
      "Página sem login aberta pelo QR. Mostra produto, nome do cliente, referência, código do desenho, OP, unidade, data e inspetor.",
    auditSnapshot:
      "Cópia imutável da OP e do cadastro no momento do registro: referência (B1_REFEREN), desenho (B1_CODDES) e cliente (pedido da OP ou última nota fiscal).",
  },
  fields: {
    customerReference:
      "Referência do cliente no cadastro TOTVS (SB1.B1_REFEREN). É o código impresso na etiqueta ao lado de CLIENTE. Item preenchido no certificado substitui este valor na etiqueta.",
    drawingCode:
      "Código do desenho do cliente no cadastro TOTVS (SB1.B1_CODDES). Aparece na leitura do QR e na auditoria; não vai para a etiqueta física.",
    customerName:
      "Nome de exibição (A1_NREDUZ, senão A1_NOME). Vem do pedido da OP quando C2_PEDIDO existe; senão, da última NF do produto. O certificado pode sobrescrever. Não é impresso na etiqueta.",
  },
} as const;
