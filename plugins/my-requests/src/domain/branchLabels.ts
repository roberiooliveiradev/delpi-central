/** Labels curtos de filial no wizard NF (códigos TOTVS 01/02). */
export function branchShortLabel(code: string): string {
  if (code === "01") return "SC";
  if (code === "02") return "ES";
  return code;
}

export function branchAriaLabel(code: string): string {
  if (code === "01") return "Santa Catarina";
  if (code === "02") return "Espírito Santo";
  return `Filial ${code}`;
}
