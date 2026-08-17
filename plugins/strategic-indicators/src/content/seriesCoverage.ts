/** Textos de cobertura da série temporal (pt-BR). */

export const seriesCoverageCopy = {
  incompleteTitle: "Série histórica incompleta",
  incompleteDescription: (params: {
    monthsRequested: number;
    monthsReturned: number;
    missingCompetences: string[];
  }) => {
    const missing =
      params.missingCompetences.length > 0
        ? ` Competências sem score materializado: ${params.missingCompetences.join(", ")}.`
        : "";
    return (
      `Foram solicitados ${params.monthsRequested} meses e a API retornou ${params.monthsReturned}.` +
      missing +
      " Use Atualizar para materializar period_scores na janela pedida."
    );
  },
} as const;
