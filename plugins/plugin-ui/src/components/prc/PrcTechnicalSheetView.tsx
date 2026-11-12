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
  linkKeyOf,
  PRC_FIELD_GROUPS,
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
const FIELD_GROUPS = PRC_FIELD_GROUPS;

export type PrcSheetChange = { path: string; reason: string };

/** Operação granular de vínculo SA5 do contrato UPDATE
 * (`requestedChanges.supplierLinkChanges`). */
export type PrcSheetLinkOp = {
  operation: "update" | "add" | "remove";
  key: { supplierCode: string; store: string };
  fields?: { partNumber?: string; catalogNumber?: string };
  supplierName?: string;
  reason?: string;
};

/** Vínculo oficial do baseline (`officialBaseline.links`). */
export type PrcSheetBaselineLink = {
  supplierCode: string;
  store: string;
  supplierName?: string;
  partNumber?: string;
  catalogNumber?: string;
};

export type PrcTechnicalSheetViewProps = {
  /** `technicalDraft` oficial do caso (candidato CREATE/UPDATE). */
  draft: Record<string, unknown> | null | undefined;
  /** Tipo da solicitação — `update` ativa a visualização de alterações
   * solicitadas (apenas campos/vínculos efetivamente envolvidos). */
  requestType?: "create" | "update";
  /** Campos alterados com a justificativa registrada no draft. */
  changedPaths?: PrcSheetChange[];
  /** Operações de vínculo solicitadas (UPDATE) — fonte única da seção
   * de fornecedores; ausência de ops oculta o card por completo. */
  supplierLinkChanges?: PrcSheetLinkOp[] | null;
  /** Vínculos oficiais do baseline (UPDATE) — identidade e «antes»
   * das operações remove/update. */
  baselineLinks?: PrcSheetBaselineLink[] | null;
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

const UNAVAILABLE_TEXT = "Não disponível";

function scalarText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  /* PRC-UX-CHANGE-01 — nunca `String(objeto)` na UI: estruturas não
   * escalares recebem estado explícito de indisponibilidade (R7/R9). */
  if (typeof value === "object") return UNAVAILABLE_TEXT;
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

/* ── PRC-UX-CHANGE-01 — modo UPDATE: visualização das alterações ── */

const SUPPLIER_OP_LABELS: Record<PrcSheetLinkOp["operation"], string> = {
  add: "Adicionar fornecedor",
  remove: "Remover vínculo",
  update: "Alterar vínculo",
};

const LINK_ATTRS = ["partNumber", "catalogNumber"] as const;
type LinkAttr = (typeof LINK_ATTRS)[number];

/** Paths que nunca entram na comparação escalar (cobertos por outras
 * seções ou não são campos de formulário). */
const NON_SCALAR_CHANGE_PATHS = new Set([
  "officialProductCode",
  "suppliers",
  "supplierLinkChanges",
]);

/** Valor «antes» tipado: baseline ausente, path ausente ou estrutura
 * não escalar → estado explícito, nunca objeto bruto (R7–R9). */
function beforeText(path: string, baselineFields: Props["baselineFields"]) {
  if (!baselineFields || !(path in baselineFields)) return UNAVAILABLE_TEXT;
  return displayValue(path, baselineFields[path]);
}

function linkAttrLabel(attr: LinkAttr): string {
  return PRC_SUPPLIER_LABELS[attr] || attr;
}

type Props = PrcTechnicalSheetViewProps;

function UpdateChangesSheet({
  draft,
  changedPaths = [],
  supplierLinkChanges,
  baselineLinks,
  specNotes,
  baselineFields,
  suppliersHeaderActions,
  fieldAdornment,
  supplierAdornment,
}: Props) {
  const data = draft || {};
  const officialCode = scalarText(data.officialProductCode);
  const scalarChanges = changedPaths.filter(
    (c) => !NON_SCALAR_CHANGE_PATHS.has(c.path),
  );
  const ops = supplierLinkChanges || [];
  const baselineByKey = new Map(
    (baselineLinks || []).map((l) => [
      linkKeyOf(l.supplierCode, l.store),
      l,
    ]),
  );
  const linkRow = (key: { supplierCode: string; store: string }) => {
    const base = baselineByKey.get(linkKeyOf(key.supplierCode, key.store));
    return {
      rowId: linkKeyOf(key.supplierCode, key.store),
      origin: "official" as const,
      supplierCode: key.supplierCode,
      store: key.store,
      supplierName: base?.supplierName || "",
      partNumber: base?.partNumber || "",
      catalogNumber: base?.catalogNumber || "",
      query: "",
    };
  };

  return (
    <>
      <PrcSheetCard title="Identificação do produto">
        <div className="delpi-prc__sheet-grid">
          <div className="delpi-prc__sheet-field">
            <div className="delpi-prc__sheet-field-label">
              <FieldLabel
                label={fieldLabel("officialProductCode")}
                hint={prcFieldHelp("officialProductCode", specNotes?.officialProductCode)}
              />
            </div>
            <div className="delpi-prc__sheet-field-value">
              {officialCode}
            </div>
          </div>
        </div>
      </PrcSheetCard>

      <PrcSheetCard title="Alterações solicitadas">
        {scalarChanges.length ? (
          <div className="delpi-prc__change-list">
            {scalarChanges.map((c) => {
              const label = fieldLabel(c.path);
              const after = displayValue(c.path, data[c.path]);
              return (
                <div
                  key={c.path}
                  id={`prc-field-${c.path}`}
                  tabIndex={-1}
                  className="delpi-prc__change-item"
                >
                  <div className="delpi-prc__sheet-field-label">
                    <FieldLabel
                      label={label}
                      hint={prcFieldHelp(c.path, specNotes?.[c.path])}
                    />
                    {fieldAdornment ? fieldAdornment(c.path, after) : null}
                  </div>
                  {c.reason ? (
                    <p className="delpi-prc__change-reason">
                      Justificativa: {c.reason}
                    </p>
                  ) : null}
                  <div className="delpi-prc__change-compare">
                    <div className="delpi-prc__change-side">
                      <span className="delpi-prc__change-side-label">
                        Antes
                      </span>
                      <span className="delpi-prc__change-side-value delpi-prc__change-side-value--before">
                        {beforeText(c.path, baselineFields)}
                      </span>
                    </div>
                    <div className="delpi-prc__change-side">
                      <span className="delpi-prc__change-side-label">
                        Solicitado
                      </span>
                      <span className="delpi-prc__change-side-value delpi-prc__change-side-value--after">
                        {after}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="delpi-prc__muted">
            Nenhuma alteração de campo registrada.
          </p>
        )}
      </PrcSheetCard>

      {ops.length ? (
        <PrcSheetCard
          title="Fornecedores"
          headerActions={suppliersHeaderActions}
        >
          <div className="delpi-prc__change-list">
            {ops.map((op, i) => {
              const base = baselineByKey.get(
                linkKeyOf(op.key.supplierCode, op.key.store),
              );
              const identity = `${op.key.supplierCode} / ${op.key.store}`;
              const name = op.supplierName || base?.supplierName || "";
              const row = linkRow(op.key);
              const attrRows =
                op.operation === "remove"
                  ? LINK_ATTRS.filter(
                      (a) => base?.[a] != null && base?.[a] !== "",
                    )
                  : LINK_ATTRS.filter(
                      (a) => op.fields && a in op.fields,
                    );
              return (
                <div
                  key={`${identity}-${i}`}
                  className="delpi-prc__change-item"
                >
                  <div className="delpi-prc__change-op-head">
                    <span
                      className={`delpi-prc__change-op-tag delpi-prc__change-op-tag--${op.operation}`}
                    >
                      {SUPPLIER_OP_LABELS[op.operation]}
                    </span>
                    <span className="delpi-prc__change-identity">
                      {identity}
                      {name ? ` — ${name}` : ""}
                    </span>
                  </div>
                  {op.reason ? (
                    <p className="delpi-prc__change-reason">
                      Justificativa: {op.reason}
                    </p>
                  ) : null}
                  {op.operation === "remove" ? (
                    <p className="delpi-prc__muted">
                      Remoção solicitada — pendente de efetivação no
                      cadastro oficial.
                    </p>
                  ) : null}
                  {attrRows.length ? (
                    <div className="delpi-prc__change-compare delpi-prc__change-compare--attrs">
                      {attrRows.map((attr) => (
                        <div
                          key={attr}
                          className="delpi-prc__change-attr"
                        >
                          <span
                            id={`prc-supplier-${op.key.supplierCode}-${op.key.store}-${attr}`}
                            className="delpi-prc__sheet-supplier-cell"
                          >
                            <strong>{linkAttrLabel(attr)}</strong>
                            {supplierAdornment
                              ? supplierAdornment(row, attr)
                              : null}
                          </span>
                          {op.operation === "update" ? (
                            <span className="delpi-prc__change-compare delpi-prc__change-compare--inline">
                              <span className="delpi-prc__change-side">
                                <span className="delpi-prc__change-side-label">
                                  Antes
                                </span>
                                <span className="delpi-prc__change-side-value delpi-prc__change-side-value--before">
                                  {scalarText(base?.[attr])}
                                </span>
                              </span>
                              <span className="delpi-prc__change-side">
                                <span className="delpi-prc__change-side-label">
                                  Solicitado
                                </span>
                                <span className="delpi-prc__change-side-value delpi-prc__change-side-value--after">
                                  {scalarText(op.fields?.[attr])}
                                </span>
                              </span>
                            </span>
                          ) : (
                            <span className="delpi-prc__change-side-value">
                              {scalarText(
                                op.operation === "add"
                                  ? op.fields?.[attr]
                                  : base?.[attr],
                              )}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </PrcSheetCard>
      ) : null}
    </>
  );
}

export function PrcTechnicalSheetView({
  requestType,
  ...rest
}: PrcTechnicalSheetViewProps) {
  if (requestType === "update") {
    return <UpdateChangesSheet requestType={requestType} {...rest} />;
  }
  return <CreateSheet {...rest} />;
}

function CreateSheet({
  draft,
  changedPaths = [],
  specNotes,
  baselineFields,
  suppliersHeaderActions,
  fieldAdornment,
  supplierAdornment,
}: Props) {
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
