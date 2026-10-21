/**
 * Consulta de CEP (F5-UX-R4) — proposta de endereço via BFF
 * (`/suppliers/postal-codes/<cep>`) e conciliação do município com o
 * catálogo Protheus CC2. O draft só recebe códigos comprovados; o IBGE
 * externo nunca é copiado para `city_code` sem match em CC2.
 */
import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import {
  fetchCatalogItems,
  type SupplierCatalogOption,
} from "./supplierCatalogs";

export type PostalAddressSuggestion = {
  postal_code: string;
  street: string;
  district: string;
  city: string;
  state: string;
  ibge_city_code: string;
  source: string;
  found: boolean;
};

export type MunicipalityReconciliation =
  | { status: "matched"; code: string; label: string }
  | { status: "multiple"; options: SupplierCatalogOption[] }
  | { status: "unmatched" };

export function normalizePostalDigits(raw: string): string {
  return raw.replace(/\D/g, "");
}

export function isCompletePostalCode(raw: string): boolean {
  return normalizePostalDigits(raw).length === 8;
}

/** `GET /suppliers/postal-codes/<8 dígitos>` — proposta ou `{found:false}`. */
export function fetchPostalCodeSuggestion(
  cepDigits: string,
  signal?: AbortSignal,
): Promise<PostalAddressSuggestion> {
  return httpGet<PostalAddressSuggestion>(
    suppliesApiUrl(`/suppliers/postal-codes/${cepDigits}`),
    { signal },
  );
}

/**
 * `CC2_CODMUN` corresponde aos 5 últimos dígitos do código IBGE de 7
 * dígitos (UF numérica + município) — comprovado em DELPI
 * (SP/50308 = São Paulo 3550308, SC/18202 = Timbó 4218202).
 */
export function deriveProtheusCityCode(ibge: string): string {
  const digits = ibge.replace(/\D/g, "");
  return digits.length >= 7 ? digits.slice(-5) : "";
}

type MunicipalityFetcher = (
  kind: "municipalities",
  opts: { query?: string; state?: string; limit?: number },
) => Promise<{ items: SupplierCatalogOption[]; has_more?: boolean }>;

function normalizeName(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .trim()
    .toUpperCase();
}

/**
 * Concilia `localidade`/`uf`/`ibge` do provider com CC2010:
 * 1) código derivado do IBGE (determinístico);
 * 2) fallback por nome normalizado dentro da UF.
 * Múltiplos candidatos retornam para escolha — nunca escolha arbitrária.
 */
export async function reconcileMunicipality(
  uf: string,
  ibge: string,
  cityName: string,
  fetcher: MunicipalityFetcher = fetchCatalogItems,
): Promise<MunicipalityReconciliation> {
  const state = uf.trim().toUpperCase();
  if (!state) return { status: "unmatched" };

  const derived = deriveProtheusCityCode(ibge);
  if (derived) {
    const env = await fetcher("municipalities", {
      state,
      query: derived,
      limit: 50,
    });
    const exact = env.items.filter((o) => o.code === derived);
    if (exact.length === 1) {
      return { status: "matched", code: exact[0].code, label: exact[0].label };
    }
  }

  const name = cityName.trim();
  if (name) {
    const env = await fetcher("municipalities", {
      state,
      query: name,
      limit: 50,
    });
    const target = normalizeName(name);
    const exactName = env.items.filter(
      (o) => normalizeName(o.label) === target,
    );
    if (exactName.length === 1) {
      return {
        status: "matched",
        code: exactName[0].code,
        label: exactName[0].label,
      };
    }
    if (env.items.length === 1) {
      return {
        status: "matched",
        code: env.items[0].code,
        label: env.items[0].label,
      };
    }
    if (env.items.length > 1) {
      return { status: "multiple", options: env.items.slice(0, 10) };
    }
  }
  return { status: "unmatched" };
}
