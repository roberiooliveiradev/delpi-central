/**
 * Glossário mínimo P0 do Portal Suprimentos (HELP-AND-ONBOARDING).
 * Sem path técnico / operationId.
 */
export type GlossaryEntry = {
  term: string;
  meaning: string;
};

export const GLOSSARY_CONTENT: readonly GlossaryEntry[] = [
  {
    term: "OTD",
    meaning:
      "On-Time Delivery — pontualidade de entrega frente ao compromisso. Indicador analítico (Visão geral / página OTD). Não confundir com a lista operacional Entregas / Atrasos (recebimentos MP no período selecionado).",
  },
  {
    term: "Data de digitação do recebimento",
    meaning:
      "Data em que o recebimento foi digitado/entrado no sistema. Em Entregas / Atrasos, o filtro de período usa essa data — não a data prometida nem a emissão do pedido de compra.",
  },
  {
    term: "ESTSEG",
    meaning:
      "Estoque de segurança — cobertura mínima planejada e déficit. Não é o saldo físico de estoque.",
  },
  {
    term: "Saldo físico",
    meaning:
      "Quantidade atual registrada no estoque do ERP para a combinação produto, unidade e armazém. Não significa saldo disponível.",
  },
  {
    term: "SC",
    meaning: "Solicitação de compras — pedido interno de compra no escopo de centro de custo e filial.",
  },
  {
    term: "Fornecedor",
    meaning:
      "Empresa do pedido de compra. Nas listas aparece com avatar de iniciais. A ficha cadastral abre pela lista Fornecedores (clique na linha).",
  },
  {
    term: "Enriquecimento cadastral",
    meaning:
      "Comparação da ficha do fornecedor com dados públicos do CNPJ (BrasilAPI, fonte externa). O resultado é uma revisão com sugestões por campo: aceitar/rejeitar é decisão sua e «Preparar atualização» gera somente um rascunho — nada é gravado no Protheus.",
  },
  {
    term: "Cadastro assistido",
    meaning:
      "Início do cadastro de fornecedor por consulta pública ao CNPJ: o Portal sugere valores com fonte e data da consulta (horário de Brasília) e você confirma campo a campo. Sugestão não é dado gravado — a criação real continua sujeita ao gate do ERP. Se já houver cadastros com o CNPJ, eles são listados com código e loja para conferência individual — sem bloquear o preenchimento. A busca por razão social fica disponível quando o provedor for homologado.",
  },
  {
    term: "Solicitante",
    meaning:
      "Pessoa que abriu a SC. Nas listas aparece com avatar de iniciais. A ficha própria está reservada e ainda não navega.",
  },
  {
    term: "PC",
    meaning:
      "Pedido de compra — documento com fornecedor após a SC. A ficha mostra itens, entrega prometida, recebimentos e a SC de origem de cada item.",
  },
  {
    term: "CPV",
    meaning: "Custo dos produtos vendidos — indicador de custo no recorte analítico.",
  },
  {
    term: "Giro",
    meaning:
      "Rotatividade do estoque. Pode aparecer em vezes (quantas voltas no período) ou em meses de cobertura — não misture as duas leituras.",
  },
  {
    term: "Filial 01",
    meaning: "Unidade Santa Catarina no escopo TOTVS do Portal.",
  },
  {
    term: "Filial 02",
    meaning: "Unidade Espírito Santo no escopo TOTVS do Portal.",
  },
  {
    term: "SA2",
    meaning:
      "Tabela de fornecedores do Protheus. O identificador é código + loja (8 dígitos); CNPJ/CPF não é chave única. O cadastro é compartilhado da empresa 01 — a filial da tela do Portal é filtro, não permissão sobre fornecedores.",
  },
  {
    term: "PTAX",
    meaning:
      "Cotação do dólar divulgada pelo Banco Central do Brasil em boletins diários (abertura, intermediárias e fechamento, de compra e venda). Na Inteligência de mercado, a conversão USD→BRL usa a média mensal da PTAX de venda no fechamento; feriados e fins de semana não têm publicação.",
  },
  {
    term: "Pink Sheet",
    meaning:
      "Relatório mensal de preços de commodities do Banco Mundial (World Bank Commodity Markets). As cotações de metais do Portal vêm desse relatório: média mensal em USD por tonelada métrica, publicada com alguns dias de defasagem — por isso o mês corrente pode aparecer vazio.",
  },
  {
    term: "Cobertura",
    meaning:
      "Na Inteligência de mercado, indica se o período tem todas as observações esperadas: Completa (todos os pontos), Parcial (faltam pontos), Sem câmbio (falta PTAX para converter) ou Sem dados.",
  },
  {
    term: "Desatualizado (stale)",
    meaning:
      "Na Inteligência de mercado, indica que a fonte está atrasada em relação ao seu ciclo de publicação — por exemplo, o Pink Sheet mensal ainda não publicou o mês esperado. Consultar um período histórico antigo não torna o dado desatualizado: o aviso reflete o atraso da fonte, não a idade da consulta.",
  },
] as const;
