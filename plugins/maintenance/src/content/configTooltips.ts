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
    "Programação de revisão periódica da ferramenta (ex.: inspeção a cada 3 meses), independente da troca de peças.",
  revisaoFerramenta:
    "Código da ferramenta no TOTVS (ex.: 23-001). Uma programação por ferramenta e filial.",
  revisaoIntervalo:
    "Periodicidade em meses calendário entre revisões (1 a 120). Ex.: 3 = revisar a cada três meses.",
  revisaoObservacao:
    "Nota opcional sobre o que verificar na revisão (checklist, pontos críticos, etc.).",
  revisaoRegistrar:
    "Marca a revisão como realizada hoje e reinicia a contagem do próximo prazo.",
} as const;
