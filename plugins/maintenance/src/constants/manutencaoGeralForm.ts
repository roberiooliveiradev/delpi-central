/** Formulário Google Apps Script — manutenção geral (máquinas, equipamentos, lâmpadas). */
export const MANUTENCAO_GERAL_FORM_URL =
  "https://script.google.com/macros/s/AKfycbx6CUMD9iqEnGatab85sHBx2drIxOKmOy5nFaRkUKsVXQa-8GNF0sl1Bm8lbFKBIToN/exec";

export function manutencaoGeralFormEmbedUrl(baseUrl = MANUTENCAO_GERAL_FORM_URL): string {
  const url = new URL(baseUrl);
  url.searchParams.set("embedded", "true");
  return url.toString();
}
