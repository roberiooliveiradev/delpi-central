import type { PropostaComercialListItem } from "../types/propostasComerciais";

function normalizeSearchTerm(value: string): string {
  return value.trim().toLowerCase();
}

function stripOvPrefix(value: string): string {
  return value.replace(/^ov\s*/i, "").trim();
}

export function filterPropostasComerciais(
  items: PropostaComercialListItem[],
  search: string,
): PropostaComercialListItem[] {
  const query = normalizeSearchTerm(search);
  if (!query) return items;

  const withoutOv = stripOvPrefix(query);

  return items.filter((item) => {
    const haystack = [
      item.proposta_interna,
      item.numero_ov,
      item.oportunidade,
      item.cliente,
    ]
      .map((value) => value.toLowerCase())
      .join(" ");

    return (
      haystack.includes(query) ||
      (withoutOv !== query && haystack.includes(withoutOv))
    );
  });
}

export function formatStatusLabel(status: string): string {
  const normalized = status.trim().toUpperCase();
  if (normalized === "A") return "Ativa";
  if (!normalized) return "—";
  return normalized;
}

export function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    return Number.isFinite(value) ? String(value) : "—";
  }
  const text = value.trim();
  return text || "—";
}

/** Lote mínimo Protheus → milheiro (÷1000), sempre 3 casas decimais. */
export function formatLoteMinimoMil(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const number = typeof value === "number" ? value : Number(String(value).replace(",", "."));
  if (!Number.isFinite(number)) return "—";
  return (number / 1000).toLocaleString("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
}
