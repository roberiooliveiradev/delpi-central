export function formatDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/** Primeiro dia do mês corrente até hoje (recorte padrão ao abrir o dashboard). */
export function currentMonthFilterRange(reference = new Date()): {
  dataInicial: string;
  dataFinal: string;
} {
  const start = new Date(reference.getFullYear(), reference.getMonth(), 1);
  return {
    dataInicial: formatDateInput(start),
    dataFinal: formatDateInput(reference),
  };
}
