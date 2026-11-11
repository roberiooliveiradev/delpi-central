/** PRC-REF-023-UI-FIX-07 — ficha técnica PRC em modo leitura.
 *
 * Única composição de apresentação dos dados técnicos do caso,
 * consumida pelo Portal Engenharia (aba Ficha técnica) e por Minhas
 * Solicitações (acompanhamento do solicitante). Render-only: não
 * conhece HTTP, AuthZ, endpoints nem identidade — os hosts injetam
 * dados oficiais da Engineering API e adornos opcionais por perfil
 * (flags de atendimento da Engenharia, ação "Editar ficha"). */

import type { ReactNode } from "react";

import { createDashboardDetailCard } from "../layout/DetailCard";
import { detailCardRichBemClasses } from "../layout/DetailCard";
import { FieldLabel } from "../help/FieldLabel";
import {
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_LABELS,
  PRC_ENUM_OPTION_LABELS,
  prcFieldHelp,
  toSupplierRows,
  type SupplierRow,
} from "../../utils/prcProductRegistration";
import { PRC_SUPPLIER_TEXT } from "./PrcSupplierForm";

const PrcSheetCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses("delpi-ui"),
  labels: { titleHelpAriaLabel: (title) => `Ajuda: ${title}` },
});

/** Mesma ordem de grupos/campos da ficha do Portal Engenharia. */
const FIELD_GROUPS: { title: string; paths: string[] }[] = [
  {
    title: "Identificação e classificação",
    paths: [
      "officialProductCode",
      "description",
      "group",
      "productKind",
      "unit",
    ],
  },
  {
    title: "Estoque e contabilidade",
    paths: [
      "defaultWarehouse",
      "accountingAccount",
      "thirdPartyProduct",
      "customerReference",
    ],
  },
];

export type PrcSheetChange = { path: string; reason: string };

export type PrcTechnicalSheetViewProps = {
  /** `technicalDraft` oficial do caso (candidato CREATE/UPDATE). */
  draft: Record<string, unknown> | null | undefined;
  /** Campos alterados com a justificativa registrada no draft. */
  changedPaths?: PrcSheetChange[];
  /** Nota do field-spec por path (fallback do help funcional). */
  specNotes?: Record<string, string | null | undefined> | null;
  /** Baseline oficial por path (UPDATE) — exibido como «antes». */
  baselineFields?: Record<string, unknown> | null;
  /** Conteúdo extra no cabeçalho do card Fornecedores
   * (ex.: «Editar ficha» da Engenharia). */
  suppliersHeaderActions?: ReactNode;
  /** Adorno por campo (ex.: flags de acompanhamento do analista). */
  fieldAdornment?: (path: string, displayValue: string) => ReactNode;
  /** Adorno por célula de vínculo (Part Number / Catálogo). */
  supplierAdornment?: (
    row: SupplierRow,
    attribute: "partNumber" | "catalogNumber",
  ) => ReactNode;
};

function scalarText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function displayValue(path: string, value: unknown): string {
  const raw = scalarText(value);
  if (raw === "—") return raw;
  return PRC_ENUM_OPTION_LABELS[path]?.[raw] ?? raw;
}

function fieldLabel(path: string): string {
  return PRC_FIELD_LABELS[path] || path;
}

export function PrcTechnicalSheetView({
  draft,
  changedPaths = [],
  specNotes,
  baselineFields,
  suppliersHeaderActions,
  fieldAdornment,
  supplierAdornment,
}: PrcTechnicalSheetViewProps) {
  const data = draft || {};
  const changed = new Set(changedPaths.map((c) => c.path));
  const reasonByPath = new Map(changedPaths.map((c) => [c.path, c.reason]));
  const suppliers = toSupplierRows(data.suppliers);
  const showShortName = suppliers.some((r) =>
    (r.supplierShortName || "").trim(),
  );

  const changeNote = (path: string): string => {
    const reason = reasonByPath.get(path) || "";
    const before =
      baselineFields && path in baselineFields
        ? ` — antes: ${scalarText(baselineFields[path])}`
        : "";
    return `${reason}${before}`;
  };

  return (
    <>
      {FIELD_GROUPS.map((group) => {
        const paths = group.paths.filter(
          (p) => p in data || p === "officialProductCode",
        );
        if (!paths.length) return null;
        return (
          <PrcSheetCard key={group.title} title={group.title}>
            <div className="delpi-prc__sheet-grid">
              {paths.map((p) => {
                const label = fieldLabel(p);
                const value = displayValue(p, data[p]);
                return (
                  <div
                    key={p}
                    id={`prc-field-${p}`}
                    tabIndex={-1}
                    className={
                      p === "description"
                        ? "delpi-prc__sheet-field delpi-prc__sheet-field--wide"
                        : "delpi-prc__sheet-field"
                    }
                  >
                    <div className="delpi-prc__sheet-field-label">
                      <FieldLabel
                        label={label}
                        hint={prcFieldHelp(p, specNotes?.[p])}
                      />
                      {p !== "officialProductCode" && fieldAdornment
                        ? fieldAdornment(p, value)
                        : null}
                    </div>
                    <div className="delpi-prc__sheet-field-value">
                      {value}
                    </div>
                  </div>
                );
              })}
            </div>
            {group.paths.some((p) => changed.has(p)) ? (
              <ul className="delpi-prc__change-notes">
                {group.paths
                  .filter((p) => changed.has(p))
                  .map((p) => (
                    <li key={p}>
                      <strong>{fieldLabel(p)}</strong> — alterado:{" "}
                      {changeNote(p)}
                    </li>
                  ))}
              </ul>
            ) : null}
          </PrcSheetCard>
        );
      })}

      <PrcSheetCard
        title="Fornecedores"
        headerActions={suppliersHeaderActions}
      >
        {suppliers.length ? (
          <table className="delpi-prc__sheet-table">
            <thead>
              <tr>
                <th>{PRC_SUPPLIER_LABELS.supplierCode}</th>
                <th>{PRC_SUPPLIER_LABELS.store}</th>
                <th>{PRC_SUPPLIER_LABELS.supplierName}</th>
                {showShortName ? <th>Nome fantasia</th> : null}
                <th title={PRC_SUPPLIER_TEXT.partNumberHint}>
                  {PRC_SUPPLIER_LABELS.partNumber}
                </th>
                <th>{`${PRC_SUPPLIER_LABELS.catalogNumber} (opcional)`}</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((r) => (
                <tr key={`${r.supplierCode}.${r.store}.${r.partNumber}`}>
                  <td>{r.supplierCode}</td>
                  <td>{r.store}</td>
                  <td>{r.supplierName}</td>
                  {showShortName ? (
                    <td>{r.supplierShortName || "—"}</td>
                  ) : null}
                  <td>
                    <span
                      id={`prc-supplier-${r.supplierCode}-${r.store}-partNumber`}
                      className="delpi-prc__sheet-supplier-cell"
                    >
                      {r.partNumber || "—"}
                      {supplierAdornment
                        ? supplierAdornment(r, "partNumber")
                        : null}
                    </span>
                  </td>
                  <td>
                    <span
                      id={`prc-supplier-${r.supplierCode}-${r.store}-catalogNumber`}
                      className="delpi-prc__sheet-supplier-cell"
                    >
                      {r.catalogNumber || "—"}
                      {supplierAdornment
                        ? supplierAdornment(r, "catalogNumber")
                        : null}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="delpi-prc__muted">Nenhum fornecedor vinculado.</p>
        )}
        {changed.has("suppliers") ? (
          <p className="delpi-prc__change-notes">
            <strong>Fornecedores</strong> — alterado: {changeNote("suppliers")}
          </p>
        ) : null}
      </PrcSheetCard>
    </>
  );
}
