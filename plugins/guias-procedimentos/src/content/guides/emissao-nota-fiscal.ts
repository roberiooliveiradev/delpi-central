import type { GuideDocument } from "../../types/guide";

/**
 * Guia V1 — Faturamento / emissão de nota fiscal.
 * Conteúdo estruturado local; trocar o loader por API futuramente.
 */
export const EMISSAO_NOTA_FISCAL_GUIDE: GuideDocument = {
  meta: {
    id: "guide-emissao-nota-fiscal",
    slug: "emissao-nota-fiscal",
    departmentId: "faturamento",
    title: "Informações necessárias para solicitação de emissão de nota fiscal",
    summary:
      "O que reunir antes de solicitar a emissão: destinatário, itens, tipo de NF, transporte e pedido de compra.",
    tags: [
      "nota fiscal",
      "faturamento",
      "NF",
      "cliente",
      "fornecedor",
      "estoque",
      "almoxarifado",
      "CIF",
      "FOB",
      "transportadora",
      "devolução",
      "amostra",
      "remessa",
      "conserto",
      "pedido de compra",
    ],
    responsibleArea: "Faturamento",
    updatedAtLabel: "A confirmar",
    readingTimeMinutes: 4,
    status: "published",
  },
  introduction:
    "Antes de solicitar a emissão de uma nota fiscal, reúna e confira todas as informações necessárias. Isso reduz correções, atrasos e devoluções da solicitação.",
  sections: [
    {
      id: "destinatario",
      title: "Dados do destinatário",
      items: [
        {
          id: "dest-codigo",
          text: "Se já estiver cadastrado, informar o código do cliente ou fornecedor.",
        },
        {
          id: "dest-cadastro",
          text: "Se não estiver cadastrado, providenciar o cadastro antes da solicitação.",
          emphasis: true,
        },
      ],
    },
    {
      id: "produtos-servicos",
      title: "Dados dos produtos ou serviços",
      items: [
        { id: "prod-codigo", text: "Código do item." },
        { id: "prod-qtd", text: "Quantidade." },
        { id: "prod-valor", text: "Valor unitário." },
        {
          id: "prod-baixa",
          text: "Informar se haverá baixa de estoque.",
          emphasis: true,
        },
        {
          id: "prod-almox",
          text: "Caso haja baixa de estoque, o material precisa estar no almoxarifado 01.",
          emphasis: true,
        },
      ],
    },
    {
      id: "tipo-nf",
      title: "Tipo de nota fiscal",
      items: [
        { id: "tipo-venda", text: "Venda." },
        { id: "tipo-devolucao", text: "Devolução." },
        { id: "tipo-amostra", text: "Amostra." },
        { id: "tipo-remessa", text: "Remessa ou retorno de conserto." },
        { id: "tipo-outros", text: "Outros." },
      ],
    },
    {
      id: "transporte",
      title: "Transporte",
      items: [
        {
          id: "trans-modalidade",
          text: "Informar a modalidade de transporte (CIF ou FOB).",
          emphasis: true,
        },
        { id: "trans-transportadora", text: "Transportadora." },
        { id: "trans-peso", text: "Peso e volumes." },
      ],
    },
    {
      id: "adicionais",
      title: "Informações adicionais",
      items: [
        {
          id: "add-pedido",
          text: "Pedido de compra, quando existir.",
          emphasis: true,
        },
      ],
    },
  ],
  checklist: [
    { id: "chk-destinatario", label: "Destinatário identificado ou cadastrado." },
    { id: "chk-itens", label: "Código dos itens informado." },
    { id: "chk-qtd-valor", label: "Quantidade e valor unitário conferidos." },
    { id: "chk-estoque", label: "Baixa de estoque definida." },
    { id: "chk-tipo-nf", label: "Tipo de nota fiscal selecionado." },
    { id: "chk-modalidade", label: "Modalidade de transporte informada." },
    { id: "chk-peso", label: "Peso e volumes informados." },
    {
      id: "chk-pedido",
      label: "Pedido de compra anexado ou informado, quando existir.",
    },
  ],
  footerNotice:
    "Em caso de dúvida sobre um caso específico, confirme as informações com o setor de Faturamento antes de enviar a solicitação.",
};
