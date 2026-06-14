import { CULTURA_DELPI_PLACEHOLDER } from "../content/culturaDelpi";
import type { CulturaDelpiContent } from "../types/culturaDelpi";

export type ParsedValor = {
  titulo: string;
  descricao: string;
};

export function displayField(value: string): string {
  return value.trim() ? value.trim() : CULTURA_DELPI_PLACEHOLDER;
}

export function isCulturaContentEmpty(content: CulturaDelpiContent): boolean {
  const valores = content.valores.map((item) => item.trim()).filter(Boolean);
  return (
    !content.proposito.trim() &&
    !content.missao.trim() &&
    !content.visao.trim() &&
    valores.length === 0
  );
}

export function parseValorItem(raw: string): ParsedValor {
  const trimmed = raw.trim();
  if (!trimmed) {
    return { titulo: "", descricao: "" };
  }

  const match = trimmed.match(/^(.+?)\s*[-–—]\s*(.+)$/);
  if (match) {
    return {
      titulo: match[1].trim(),
      descricao: match[2].trim(),
    };
  }

  return { titulo: trimmed, descricao: "" };
}

export function formatUpdatedAtFooter(updatedAt: string | null): string | null {
  if (!updatedAt) return null;

  const date = new Date(updatedAt);
  if (Number.isNaN(date.getTime())) return null;

  const datePart = date.toLocaleDateString("pt-BR");
  const timePart = date.toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return `Última atualização: ${datePart} às ${timePart}`;
}
