/** Textos dos balões explicativos — tela Configuração (mini-aplicadores). */
export const CONFIG_TOOLTIPS = {
  motivoDescricao:
    "Nome do motivo de troca usado no histórico de reposições (ex.: desgaste, quebra, ajuste).",
  excluirPreventiva:
    "Reposições com este motivo não entram na média de golpes nem no ranking preventivo da peça.",
  statusDescricao:
    "Rótulo exibido no relatório preventivo quando a regra for atendida (ex.: CRÍTICO, ATENÇÃO, OK).",
  statusOperador:
    "Compara o percentual de uso atual com a média histórica de golpes entre reposições.",
  statusPercentual:
    "Limite em relação à média (ex.: 80 significa 80% da média histórica de golpes).",
  motivosSection:
    "Cadastro dos motivos disponíveis ao registrar uma reposição de peça na ferramenta.",
  statusSection:
    "Define como cada par ferramenta/peça é classificado no relatório preventivo.",
  revisaoSection:
    "Programação de revisão periódica desta ferramenta no módulo preventivo (ex.: inspeção a cada 3 meses).",
  revisaoFerramenta:
    "Código da ferramenta atual no TOTVS — a programação fica vinculada a ela na filial.",
  revisaoReferencia:
    "Data da última revisão feita ou marco inicial do ciclo. Vazio usa a data de criação da programação.",
  revisaoIntervalo:
    "Periodicidade em meses calendário entre revisões (1 a 120). Ex.: 3 = revisar a cada três meses.",
  revisaoObservacao:
    "Nota opcional sobre o que verificar na revisão (checklist, pontos críticos, etc.).",
  revisaoRegistrar:
    "Marca a revisão como feita na data informada e recalcula a próxima revisão a partir dela.",
  revisaoHistorico:
    "Registros de revisões marcadas como feitas nesta ferramenta (a partir de agora).",
} as const;
