import type { ChatContextChip } from "./ChatContextBar";

export function buildContextChipQuery(chip: ChatContextChip): string | null {
  const value = String(chip.value ?? "").trim();

  if (!value) {
    return null;
  }

  switch (chip.kind) {
    case "product":
      return `qual o estoque do produto ${value}?`;
    case "branch":
      return `filtre pela filial ${value}`;
    case "format":
      if (value === "table") {
        return "mostre em tabela";
      }

      return null;
    case "tone":
      if (value === "direct") {
        return "responda de forma mais direta";
      }

      if (value === "simple") {
        return "use linguagem mais simples";
      }

      return null;
    case "preference":
      if (value === "final_only") {
        return "entregue só a versão final, sem explicações longas";
      }

      return null;
    default:
      return null;
  }
}
