/** PRC-REF-023-REF022-GRANULAR-CORRECTION-09 — devolução e correção
 * granulares compartilhadas entre Portal Engenharia e Minhas
 * Solicitações.
 *
 * Dois blocos, mesmo contrato de alvos da Engineering API:
 *
 * - ``PrcCorrectionTargetSelector`` — usado pelo analista no modal de
 *   devolução: checklist de campos escalares + tabela de fornecedores
 *   com seleção por célula (Part Number / Catálogo / vínculo integral)
 *   e motivo obrigatório por alvo. A identidade técnica do vínculo
 *   (supplierCode/store/targetAttribute) sai da ficha — nunca de input
 *   do analista.
 *
 * - ``PrcReturnedFieldsEditor`` — usado pelo solicitante no card de
 *   correção: cada alvo devolvido vira editor apropriado (select de
 *   catálogo quando o spec traz enumValues), somente as células
 *   devolvidas dos fornecedores ficam editáveis, e o payload final
 *   respeita ``mode: changed|confirmed`` do PATCH /returned-fields.
 *
 * Somente apresentação + montagem de payload: AuthZ, allowlist de
 * alvos, CAS, idempotência e estado ``needs_correction`` são decididos
 * pelo backend. */

import { useMemo, useState } from "react";

import { ActionButton } from "../actions/ActionButton";
import { FormSelectControl } from "../forms/FormSelectControl";
import {
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_LABELS,
  supplierRowsToPayload,
  toSupplierRows,
  type SupplierRow,
} from "../../utils/prcProductRegistration";

/* ------------------------------------------------------------------ */
/* Contratos                                                           */
/* ------------------------------------------------------------------ */

/** Alvo de devolução — contrato oficial POST …/return-for-correction. */
export type PrcCorrectionTargetInput = {
  targetType: "FIELD" | "SUPPLIER_LINK";
  targetPath?: string | null;
  targetAttribute?: string | null;
  supplierKey?: { supplierCode: string; store: string } | null;
  reason: string;
};

/** Alvo devolvido — wire shape público de ``correctionExchange``. */
export type PrcCorrectionTargetWire = {
  id?: string;
  ordinal?: number;
  targetType: string;
  targetPath?: string | null;
  targetAttribute?: string | null;
  supplierKey?: { supplierCode: string; store: string } | null;
  targetKey?: string | null;
  targetLabel?: string | null;
  reason: string;
  baselineValue?: unknown;
  addressedMode?: "changed" | "confirmed" | null;
};

/** Vínculo exibido nas tabelas de seleção/correção. */
export type PrcCorrectionLink = {
  supplierCode: string;
  store: string;
  supplierName?: string | null;
  supplierShortName?: string | null;
  partNumber?: string | null;
  catalogNumber?: string | null;
};

/** Campo elegível à devolução (path oficial + label). ``group``
 * agrupa o campo em uma seção do seletor (ex.: identificação,
 * estoque/contabilidade) — sem group o campo fica na seção padrão. */
export type PrcCorrectionFieldOption = {
  path: string;
  label: string;
  group?: string | null;
};

/** Spec mínimo para renderizar o editor correto de um campo devolvido. */
export type PrcFieldSpecLike = {
  path: string;
  kind: string;
  enumValues?: string[] | null;
  maxLength?: number;
  note?: string | null;
};

/** Entrada do PATCH /returned-fields — ``mode`` é parte do contrato. */
export type PrcReturnedFieldChange = {
  path: string;
  proposedValue: unknown;
  reason: string;
  mode: "changed" | "confirmed";
};

export const PRC_SUPPLIER_EDITABLE_ATTRIBUTES = [
  "partNumber",
  "catalogNumber",
] as const;

export type PrcSupplierEditableAttribute =
  (typeof PRC_SUPPLIER_EDITABLE_ATTRIBUTES)[number];

/* ------------------------------------------------------------------ */
/* Helpers puros — seleção da devolução                                */
/* ------------------------------------------------------------------ */

export function prcSupplierLinkKey(code: string, store: string): string {
  return `${String(code ?? "").trim()}|${String(store ?? "").trim()}`;
}

/** Checkboxes de uma linha de fornecedor no seletor. */
export type PrcSupplierCellSelection = {
  link: { selected: boolean; reason: string };
  partNumber: { selected: boolean; reason: string };
  catalogNumber: { selected: boolean; reason: string };
};

export type PrcCorrectionSelection = {
  /** ``path`` → seleção + motivo individual. */
  fields: Record<string, { selected: boolean; reason: string }>;
  /** ``code|store`` → seleção por vínculo/célula + motivos. */
  suppliers: Record<string, PrcSupplierCellSelection>;
};

export function emptyCorrectionSelection(): PrcCorrectionSelection {
  return { fields: {}, suppliers: {} };
}

/** Dedup de vínculos por ``(supplierCode, store)`` — zeros à esquerda
 * são preservados, nunca normalizados. */
export function dedupeCorrectionLinks(
  links: PrcCorrectionLink[] | null | undefined,
): PrcCorrectionLink[] {
  const seen = new Set<string>();
  const out: PrcCorrectionLink[] = [];
  for (const l of links || []) {
    const code = String(l.supplierCode || "").trim();
    const store = String(l.store || "").trim();
    if (!code || !store) continue;
    const key = prcSupplierLinkKey(code, store);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ ...l, supplierCode: code, store });
  }
  return out;
}

export type PrcCorrectionSelectionSummary = {
  scalarFields: number;
  suppliers: number;
  supplierAttributes: number;
  totalTargets: number;
  /** Primeiro motivo ausente (label) — bloqueia o envio. */
  firstMissingReason: string | null;
};

export function summarizeCorrectionSelection(
  selection: PrcCorrectionSelection,
  suppliers: PrcCorrectionLink[],
): PrcCorrectionSelectionSummary {
  const fieldPaths = Object.keys(selection.fields).filter(
    (p) => selection.fields[p]?.selected,
  );
  let supplierCount = 0;
  let linkTargets = 0;
  let attrCount = 0;
  let firstMissing: string | null = null;
  for (const p of fieldPaths) {
    const reason = (selection.fields[p]?.reason || "").trim();
    if (reason.length < 3 && !firstMissing) {
      firstMissing = PRC_FIELD_LABELS[p] || p;
    }
  }
  const byKey = new Map(
    dedupeCorrectionLinks(suppliers).map((l) => [
      prcSupplierLinkKey(l.supplierCode, l.store),
      l,
    ]),
  );
  for (const [key, sel] of Object.entries(selection.suppliers)) {
    const link = byKey.get(key);
    const display = link
      ? `Fornecedor ${link.supplierCode} / ${link.store}`
      : `Fornecedor ${key}`;
    let touched = false;
    if (sel.link.selected) {
      touched = true;
      linkTargets += 1;
      if ((sel.link.reason || "").trim().length < 3 && !firstMissing) {
        firstMissing = display;
      }
    }
    for (const attr of PRC_SUPPLIER_EDITABLE_ATTRIBUTES) {
      if (!sel[attr].selected) continue;
      touched = true;
      attrCount += 1;
      if ((sel[attr].reason || "").trim().length < 3 && !firstMissing) {
        firstMissing = `${PRC_SUPPLIER_LABELS[attr]} — ${display}`;
      }
    }
    if (touched) supplierCount += 1;
  }
  return {
    scalarFields: fieldPaths.length,
    suppliers: supplierCount,
    supplierAttributes: attrCount,
    totalTargets: fieldPaths.length + linkTargets + attrCount,
    firstMissingReason: firstMissing,
  };
}

/* ------------------------------------------------------------------ */
/* FIX-12 — erros por alvo (identidade estável, nunca índice)           */
/* ------------------------------------------------------------------ */

/** Chave de erro de campo escalar: ``field|path``. */
export function correctionFieldTargetKey(path: string): string {
  return `field|${path}`;
}

/** Chave de erro de célula de fornecedor:
 * ``supplier|code|store|cell`` (cell = link|partNumber|catalogNumber). */
export function correctionSupplierTargetKey(
  link: { supplierCode: string; store: string },
  cell: "link" | PrcSupplierEditableAttribute,
): string {
  return `supplier|${prcSupplierLinkKey(link.supplierCode, link.store)}|${cell}`;
}

/** Mapa ``targetKey → mensagem`` exibido junto ao campo. */
export type PrcCorrectionTargetErrors = Record<string, string>;

/** Ordem visual dos alvos — usada para focar o primeiro inválido. */
export function orderedCorrectionTargetKeys(
  fieldOptions: PrcCorrectionFieldOption[],
  suppliers: PrcCorrectionLink[],
): string[] {
  const keys = fieldOptions.map((o) => correctionFieldTargetKey(o.path));
  for (const link of dedupeCorrectionLinks(suppliers)) {
    keys.push(correctionSupplierTargetKey(link, "partNumber"));
    keys.push(correctionSupplierTargetKey(link, "catalogNumber"));
    keys.push(correctionSupplierTargetKey(link, "link"));
  }
  return keys;
}

/** Id do controle (textarea/input de motivo) associado a um targetKey
 * no seletor — permite foco programático no primeiro inválido. */
export function correctionReasonControlId(
  idPrefix: string,
  targetKey: string,
): string {
  const [kind, ...rest] = targetKey.split("|");
  if (kind === "field") {
    return `${idPrefix}-reason-field-${rest.join("|")}`;
  }
  const [code, store, cell] = rest;
  return `${idPrefix}-reason-sup-${code}-${store}-${cell}`;
}

/** Primeira chave inválida na ordem visual, ou null. */
export function firstInvalidCorrectionTarget(
  errors: PrcCorrectionTargetErrors,
  orderedKeys: string[],
): string | null {
  for (const key of orderedKeys) {
    if (errors[key]) return key;
  }
  return Object.keys(errors)[0] || null;
}

/** Remove erros resolvidos (motivo válido ou alvo desmarcado) e
 * mantém os demais — limpeza incremental sem reflagir o usuário. */
export function pruneCorrectionErrors(
  errors: PrcCorrectionTargetErrors,
  selection: PrcCorrectionSelection,
  fieldOptions: PrcCorrectionFieldOption[],
  suppliers: PrcCorrectionLink[],
): PrcCorrectionTargetErrors {
  const validPaths = new Set(fieldOptions.map((o) => o.path));
  const byKey = new Map(
    dedupeCorrectionLinks(suppliers).map((l) => [
      prcSupplierLinkKey(l.supplierCode, l.store),
      l,
    ]),
  );
  const next: PrcCorrectionTargetErrors = {};
  for (const [key, message] of Object.entries(errors)) {
    const [kind, ...rest] = key.split("|");
    if (kind === "field") {
      const path = rest.join("|");
      const sel = selection.fields[path];
      if (
        sel?.selected &&
        validPaths.has(path) &&
        (sel.reason || "").trim().length < 3
      ) {
        next[key] = message;
      }
      continue;
    }
    if (kind === "supplier") {
      const [code, store, cell] = rest;
      const link = byKey.get(prcSupplierLinkKey(code, store));
      const sel = selection.suppliers[prcSupplierLinkKey(code, store)];
      const cellSel =
        cell === "link"
          ? sel?.link
          : sel?.[cell as PrcSupplierEditableAttribute];
      if (link && cellSel?.selected && (cellSel.reason || "").trim().length < 3) {
        next[key] = message;
      }
    }
  }
  return next;
}

export type PrcCorrectionSelectionValidation = {
  targets: PrcCorrectionTargetInput[] | null;
  /** Erro global (nenhum alvo selecionado) — sem campo responsável. */
  error: string;
  /** Erros por alvo — chave estável, nunca índice. */
  errors: PrcCorrectionTargetErrors;
};

/** Constrói os alvos do contrato a partir da seleção — vínculo
 * integral (link) e cada atributo são alvos independentes. Retorna
 * ``null`` quando a seleção é inválida para envio. FIX-12: coleta
 * TODOS os alvos inválidos (não aborta no primeiro) para a
 * apresentação contextual por campo. */
export function correctionTargetsFromSelection(
  selection: PrcCorrectionSelection,
  fieldOptions: PrcCorrectionFieldOption[],
  suppliers: PrcCorrectionLink[],
): PrcCorrectionSelectionValidation {
  const targets: PrcCorrectionTargetInput[] = [];
  const errors: PrcCorrectionTargetErrors = {};
  const validPaths = new Set(fieldOptions.map((o) => o.path));
  for (const [path, sel] of Object.entries(selection.fields)) {
    if (!sel.selected || !validPaths.has(path)) continue;
    const reason = (sel.reason || "").trim();
    if (reason.length < 3) {
      errors[correctionFieldTargetKey(path)] =
        `Informe o motivo (mín. 3 caracteres) para «${PRC_FIELD_LABELS[path] || path}».`;
      continue;
    }
    targets.push({
      targetType: "FIELD",
      targetPath: path,
      reason,
    });
  }
  const byKey = new Map(
    dedupeCorrectionLinks(suppliers).map((l) => [
      prcSupplierLinkKey(l.supplierCode, l.store),
      l,
    ]),
  );
  for (const [key, sel] of Object.entries(selection.suppliers)) {
    const link = byKey.get(key);
    if (!link) continue;
    const supplierKey = {
      supplierCode: link.supplierCode,
      store: link.store,
    };
    const display = `Fornecedor ${link.supplierCode} / ${link.store}`;
    if (sel.link.selected) {
      const reason = (sel.link.reason || "").trim();
      if (reason.length < 3) {
        errors[correctionSupplierTargetKey(link, "link")] =
          `Informe o motivo (mín. 3 caracteres) para «${display}».`;
      } else {
        targets.push({
          targetType: "SUPPLIER_LINK",
          targetPath: "suppliers",
          targetAttribute: null,
          supplierKey,
          reason,
        });
      }
    }
    for (const attr of PRC_SUPPLIER_EDITABLE_ATTRIBUTES) {
      if (!sel[attr].selected) continue;
      const reason = (sel[attr].reason || "").trim();
      if (reason.length < 3) {
        errors[correctionSupplierTargetKey(link, attr)] =
          `Informe o motivo (mín. 3 caracteres) para «${PRC_SUPPLIER_LABELS[attr]} — ${display}».`;
        continue;
      }
      targets.push({
        targetType: "SUPPLIER_LINK",
        targetPath: "suppliers",
        targetAttribute: attr,
        supplierKey,
        reason,
      });
    }
  }
  if (!targets.length && !Object.keys(errors).length) {
    return {
      targets: null,
      error: "Selecione ao menos um campo para devolver.",
      errors,
    };
  }
  if (Object.keys(errors).length) {
    return { targets: null, error: "", errors };
  }
  return { targets, error: "", errors };
}

/* ------------------------------------------------------------------ */
/* Helpers puros — correção do solicitante                             */
/* ------------------------------------------------------------------ */

/** ``code|store`` → atributos devolvidos. Alvo sem ``targetAttribute``
 * (vínculo integral) autoriza os dois atributos — mesma regra do
 * backend (``supplier_link_targets_index``). A identidade do vínculo
 * nunca é liberada. */
export function returnedSupplierAttrMap(
  targets: PrcCorrectionTargetWire[] | null | undefined,
): Map<string, Set<PrcSupplierEditableAttribute>> {
  const map = new Map<string, Set<PrcSupplierEditableAttribute>>();
  for (const t of targets || []) {
    if (t.targetType !== "SUPPLIER_LINK" || !t.supplierKey) continue;
    const key = prcSupplierLinkKey(
      t.supplierKey.supplierCode,
      t.supplierKey.store,
    );
    if (key === "|") continue;
    const set = map.get(key) || new Set<PrcSupplierEditableAttribute>();
    const attr = (t.targetAttribute || "").trim();
    if (
      attr === "partNumber" ||
      attr === "catalogNumber"
    ) {
      set.add(attr);
    } else {
      set.add("partNumber");
      set.add("catalogNumber");
    }
    map.set(key, set);
  }
  return map;
}

/** ``code|store|attr`` → motivo informado pela Engenharia. */
export function returnedSupplierReasonMap(
  targets: PrcCorrectionTargetWire[] | null | undefined,
): Map<string, string> {
  const map = new Map<string, string>();
  for (const t of targets || []) {
    if (t.targetType !== "SUPPLIER_LINK" || !t.supplierKey) continue;
    const key = `${prcSupplierLinkKey(
      t.supplierKey.supplierCode,
      t.supplierKey.store,
    )}|${(t.targetAttribute || "").trim() || "link"}`;
    map.set(key, t.reason);
  }
  return map;
}

export function fieldTargetsOf(
  targets: PrcCorrectionTargetWire[] | null | undefined,
): PrcCorrectionTargetWire[] {
  return (targets || []).filter(
    (t) => t.targetType === "FIELD" && Boolean(t.targetPath),
  );
}

export function hasSupplierTargets(
  targets: PrcCorrectionTargetWire[] | null | undefined,
): boolean {
  return (targets || []).some(
    (t) =>
      t.targetType === "SUPPLIER_LINK" &&
      Boolean(
        t.supplierKey &&
          t.supplierKey.supplierCode &&
          t.supplierKey.store,
      ),
  );
}

function scalarCurrent(draft: Record<string, unknown>, path: string): string {
  const v = draft[path];
  return v === null || v === undefined ? "" : String(v);
}

export type PrcReturnedChangesResult = {
  changes: PrcReturnedFieldChange[] | null;
  error: string;
  /** FIX-12 — erros por alvo: ``field|path`` (justificativa),
   * ``supplier|code|store|partNumber`` (PN obrigatório) e
   * ``suppliers`` (justificativa do grupo de fornecedores). */
  errors: PrcCorrectionTargetErrors;
};

/** Monta o payload do PATCH /returned-fields cobrindo TODOS os alvos
 * (reenvio exige ``all_targets_addressed``):
 * - FIELD alterado sai ``changed`` e exige justificativa do
 *   solicitante; FIELD mantido sai ``confirmed`` (endereça o alvo sem
 *   patch de valor);
 * - fornecedores: ``changed`` só endereça os vínculos alterados no
 *   backend — por isso, quando há alteração, enviamos também uma
 *   entrada ``confirmed`` que endereça os vínculos devolvidos e
 *   mantidos. A allowlist granular vínculo+atributo é revalidada no
 *   backend em todos os casos. */
export function buildReturnedChanges(input: {
  targets: PrcCorrectionTargetWire[];
  draft: Record<string, unknown>;
  supplierRows: SupplierRow[];
  fieldValues: Record<string, string>;
  justifications: Record<string, string>;
  supplierJustification?: string;
}): PrcReturnedChangesResult {
  const changes: PrcReturnedFieldChange[] = [];
  const errors: PrcCorrectionTargetErrors = {};
  const fieldTargets = fieldTargetsOf(input.targets);
  for (const t of fieldTargets) {
    const path = String(t.targetPath || "");
    const current = scalarCurrent(input.draft, path);
    const next = (input.fieldValues[path] ?? current).trim();
    const dirty = next !== current.trim() && next !== "";
    const justification = (input.justifications[path] || "").trim();
    if (dirty && justification.length < 3) {
      errors[correctionFieldTargetKey(path)] =
        `Informe a justificativa da correção para «${PRC_FIELD_LABELS[path] || path}».`;
      continue;
    }
    const reason =
      justification || String(t.reason || "").trim() || "Correção do solicitante.";
    changes.push({
      path,
      proposedValue: dirty ? next : input.draft[path],
      reason,
      mode: dirty ? "changed" : "confirmed",
    });
  }
  if (hasSupplierTargets(input.targets)) {
    const current = toSupplierRows(input.draft.suppliers);
    const currentByKey = new Map(
      current.map((r) => [
        prcSupplierLinkKey(r.supplierCode, r.store),
        r,
      ]),
    );
    let anyChanged = false;
    for (const row of input.supplierRows) {
      const key = prcSupplierLinkKey(row.supplierCode, row.store);
      const base = currentByKey.get(key);
      if (!base) continue;
      for (const attr of PRC_SUPPLIER_EDITABLE_ATTRIBUTES) {
        if (
          row[attr].trim() !== (base[attr] || "").trim()
        ) {
          anyChanged = true;
        }
      }
    }
    /* Vínculo alterado exige Part Number válido (regra FIX-01). */
    if (anyChanged) {
      const missing = input.supplierRows.findIndex((row) => {
        const key = prcSupplierLinkKey(row.supplierCode, row.store);
        const base = currentByKey.get(key);
        if (!base) return false;
        const touched = PRC_SUPPLIER_EDITABLE_ATTRIBUTES.some(
          (attr) => row[attr].trim() !== (base[attr] || "").trim(),
        );
        return touched && !row.partNumber.trim();
      });
      if (missing >= 0) {
        const row = input.supplierRows[missing];
        errors[
          correctionSupplierTargetKey(
            { supplierCode: row.supplierCode, store: row.store },
            "partNumber",
          )
        ] =
          `Fornecedor ${row.supplierCode} / ${row.store}: Part Number é obrigatório para alterar o vínculo.`;
      }
    }
    const firstTarget = (input.targets || []).find(
      (t) => t.targetType === "SUPPLIER_LINK",
    );
    if (anyChanged && !Object.keys(errors).length) {
      const justification = (input.supplierJustification || "").trim();
      if (justification.length < 3) {
        errors["suppliers"] =
          "Informe a justificativa da correção dos fornecedores.";
      } else {
        changes.push({
          path: "suppliers",
          proposedValue: supplierRowsToPayload(input.supplierRows),
          reason: justification,
          mode: "changed",
        });
        /* ``changed`` só endereça vínculos alterados; o ``confirmed``
         * abaixo endereça os demais vínculos devolvidos e mantidos. */
        changes.push({
          path: "suppliers",
          proposedValue: supplierRowsToPayload(input.supplierRows),
          reason: justification,
          mode: "confirmed",
        });
      }
    } else if (anyChanged) {
      /* Erros já registrados (PN ausente) — não empilha justificativa. */
    } else {
      const reason =
        (input.supplierJustification || "").trim() ||
        String(firstTarget?.reason || "").trim() ||
        "Correção do solicitante.";
      changes.push({
        path: "suppliers",
        proposedValue: supplierRowsToPayload(input.supplierRows),
        reason,
        mode: "confirmed",
      });
    }
  }
  if (!changes.length && !Object.keys(errors).length) {
    return {
      changes: null,
      error: "Nenhum campo devolvido para corrigir.",
      errors,
    };
  }
  if (Object.keys(errors).length) {
    return { changes: null, error: "", errors };
  }
  return { changes, error: "", errors };
}

/* ------------------------------------------------------------------ */
/* Seletor de alvos — modal da Engenharia                              */
/* ------------------------------------------------------------------ */

export function PrcCorrectionTargetSelector({
  fieldOptions,
  suppliers,
  selection,
  onChange,
  busy,
  draft,
  errors,
  idPrefix = "prc-return",
}: {
  fieldOptions: PrcCorrectionFieldOption[];
  suppliers: PrcCorrectionLink[];
  selection: PrcCorrectionSelection;
  onChange: (next: PrcCorrectionSelection) => void;
  busy?: boolean;
  /** Ficha atual — mostra "Atual:" por campo (vazio também é alvo). */
  draft?: Record<string, unknown> | null;
  /** FIX-12 — erros por targetKey (campo/célula) exibidos junto ao
   * motivo correspondente; o consumidor limpa ao corrigir/desmarcar. */
  errors?: PrcCorrectionTargetErrors;
  idPrefix?: string;
}) {
  const links = useMemo(() => dedupeCorrectionLinks(suppliers), [suppliers]);
  const multiple = links.length > 1;
  const summary = useMemo(
    () => summarizeCorrectionSelection(selection, links),
    [selection, links],
  );

  const toggleField = (path: string, checked: boolean) => {
    onChange({
      ...selection,
      fields: {
        ...selection.fields,
        [path]: { selected: checked, reason: selection.fields[path]?.reason || "" },
      },
    });
  };
  const setFieldReason = (path: string, reason: string) => {
    onChange({
      ...selection,
      fields: {
        ...selection.fields,
        [path]: { selected: true, reason },
      },
    });
  };
  const cellOf = (key: string): PrcSupplierCellSelection =>
    selection.suppliers[key] || {
      link: { selected: false, reason: "" },
      partNumber: { selected: false, reason: "" },
      catalogNumber: { selected: false, reason: "" },
    };
  const toggleCell = (
    link: PrcCorrectionLink,
    cell: "link" | PrcSupplierEditableAttribute,
    checked: boolean,
  ) => {
    const key = prcSupplierLinkKey(link.supplierCode, link.store);
    const cur = cellOf(key);
    onChange({
      ...selection,
      suppliers: {
        ...selection.suppliers,
        [key]: { ...cur, [cell]: { ...cur[cell], selected: checked } },
      },
    });
  };
  const setCellReason = (
    link: PrcCorrectionLink,
    cell: "link" | PrcSupplierEditableAttribute,
    reason: string,
  ) => {
    const key = prcSupplierLinkKey(link.supplierCode, link.store);
    const cur = cellOf(key);
    onChange({
      ...selection,
      suppliers: {
        ...selection.suppliers,
        [key]: { ...cur, [cell]: { selected: true, reason } },
      },
    });
  };

  const selectedCellReasons: Array<{
    key: string;
    cell: "link" | PrcSupplierEditableAttribute;
    link: PrcCorrectionLink;
    label: string;
  }> = [];
  for (const link of links) {
    const key = prcSupplierLinkKey(link.supplierCode, link.store);
    const sel = cellOf(key);
    const display = `Fornecedor ${link.supplierCode} / ${link.store}`;
    if (sel.link.selected) {
      selectedCellReasons.push({ key, cell: "link", link, label: display });
    }
    for (const attr of PRC_SUPPLIER_EDITABLE_ATTRIBUTES) {
      if (sel[attr].selected) {
        selectedCellReasons.push({
          key,
          cell: attr,
          link,
          label: `${PRC_SUPPLIER_LABELS[attr]} — ${display}`,
        });
      }
    }
  }

  const fieldGroups = useMemo(() => {
    const map = new Map<string, PrcCorrectionFieldOption[]>();
    for (const opt of fieldOptions) {
      const g = (opt.group || "").trim() || "Campos da ficha";
      const list = map.get(g) || [];
      list.push(opt);
      map.set(g, list);
    }
    return [...map.entries()];
  }, [fieldOptions]);

  const renderField = (opt: PrcCorrectionFieldOption) => {
    const sel = selection.fields[opt.path];
    const checked = Boolean(sel?.selected);
    const current = draft ? scalarCurrent(draft, opt.path) : "";
    return (
      <div key={opt.path} className="delpi-prc__correction-field">
        <label className="delpi-prc__correction-check">
          <input
            type="checkbox"
            id={`${idPrefix}-field-${opt.path}`}
            checked={checked}
            disabled={busy}
            onChange={(e) => toggleField(opt.path, e.target.checked)}
          />
          <span>{opt.label}</span>
        </label>
        {draft ? (
          <p className="delpi-prc__correction-current">
            Atual: {current || "— (vazio)"}
          </p>
        ) : null}
        {checked ? (
          <label className="delpi-prc__correction-reason">
            <span className="delpi-prc__muted">
              Motivo da correção — {opt.label}
            </span>
            {(() => {
              const key = correctionFieldTargetKey(opt.path);
              const message = errors?.[key];
              const reasonId = `${idPrefix}-reason-field-${opt.path}`;
              return (
                <>
                  <textarea
                    id={reasonId}
                    value={sel?.reason || ""}
                    disabled={busy}
                    required
                    maxLength={1000}
                    rows={2}
                    aria-invalid={message ? true : undefined}
                    aria-describedby={
                      message ? `${reasonId}-error` : undefined
                    }
                    onChange={(e) =>
                      setFieldReason(opt.path, e.target.value)
                    }
                  />
                  {message ? (
                    <p
                      id={`${reasonId}-error`}
                      className="delpi-prc__field-error"
                      role="alert"
                    >
                      {message}
                    </p>
                  ) : null}
                </>
              );
            })()}
          </label>
        ) : null}
      </div>
    );
  };

  return (
    <div className="delpi-prc__correction-selector">
      {fieldGroups.map(([title, opts]) => (
        <fieldset key={title} className="delpi-prc__correction-group">
          <legend>{title}</legend>
          <div className="delpi-prc__correction-field-list">
            {opts.map(renderField)}
          </div>
        </fieldset>
      ))}

      <fieldset className="delpi-prc__correction-group">
        <legend>Tabelas e relacionamentos — Fornecedores</legend>
        {!links.length ? (
          <p className="delpi-prc__muted">
            Nenhum registro na tabela — não há vínculos para devolver.
          </p>
        ) : (
          <div className="delpi-prc__supplier-table-wrap">
            <table className="delpi-prc__supplier-table delpi-prc__correction-table">
              <caption className="delpi-prc__sr-only">
                Seleção de atributos de fornecedores a devolver
              </caption>
              <thead>
                <tr>
                  <th scope="col">Código</th>
                  <th scope="col">Loja</th>
                  <th scope="col">Razão social</th>
                  <th scope="col">Nome fantasia</th>
                  <th scope="col">{PRC_SUPPLIER_LABELS.partNumber}</th>
                  <th scope="col">{PRC_SUPPLIER_LABELS.catalogNumber}</th>
                  <th scope="col">Vínculo</th>
                </tr>
              </thead>
              <tbody>
                {links.map((link) => {
                  const key = prcSupplierLinkKey(
                    link.supplierCode,
                    link.store,
                  );
                  const sel = cellOf(key);
                  const cellId = (cell: string) =>
                    `${idPrefix}-sup-${link.supplierCode}-${link.store}-${cell}`;
                  return (
                    <tr key={key} data-link-key={key}>
                      <td data-label="Código">{link.supplierCode}</td>
                      <td data-label="Loja">{link.store}</td>
                      <td data-label="Razão social">
                        {link.supplierName || "—"}
                      </td>
                      <td data-label="Nome fantasia">
                        {link.supplierShortName || "—"}
                      </td>
                      <td
                        data-label={PRC_SUPPLIER_LABELS.partNumber}
                        className="delpi-prc__correction-cell"
                      >
                        <label className="delpi-prc__correction-check">
                          <input
                            type="checkbox"
                            id={cellId("partNumber")}
                            checked={sel.partNumber.selected}
                            disabled={busy}
                            onChange={(e) =>
                              toggleCell(link, "partNumber", e.target.checked)
                            }
                          />
                          <span className="delpi-prc__muted">
                            {link.partNumber || "—"}
                          </span>
                        </label>
                      </td>
                      <td
                        data-label={PRC_SUPPLIER_LABELS.catalogNumber}
                        className="delpi-prc__correction-cell"
                      >
                        <label className="delpi-prc__correction-check">
                          <input
                            type="checkbox"
                            id={cellId("catalogNumber")}
                            checked={sel.catalogNumber.selected}
                            disabled={busy}
                            onChange={(e) =>
                              toggleCell(
                                link,
                                "catalogNumber",
                                e.target.checked,
                              )
                            }
                          />
                          <span className="delpi-prc__muted">
                            {link.catalogNumber || "—"}
                          </span>
                        </label>
                      </td>
                      <td
                        data-label="Vínculo"
                        className="delpi-prc__correction-cell"
                      >
                        <input
                          type="checkbox"
                          id={cellId("link")}
                          aria-label={
                            multiple
                              ? `Devolver vínculo ${link.supplierCode} / ${link.store}`
                              : "Devolver vínculo do fornecedor"
                          }
                          checked={sel.link.selected}
                          disabled={busy}
                          onChange={(e) =>
                            toggleCell(link, "link", e.target.checked)
                          }
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {selectedCellReasons.map(({ key, cell, link, label }) => {
            const sel = cellOf(key);
            const targetKey = correctionSupplierTargetKey(link, cell);
            const message = errors?.[targetKey];
            const reasonId = `${idPrefix}-reason-sup-${link.supplierCode}-${link.store}-${cell}`;
            return (
              <label
                key={`${key}-${cell}`}
                className="delpi-prc__correction-reason"
              >
                <span className="delpi-prc__muted">
                  Motivo da correção — {label}
                </span>
                <textarea
                  id={reasonId}
                  value={sel[cell].reason}
                  disabled={busy}
                  required
                  maxLength={1000}
                  rows={2}
                  aria-invalid={message ? true : undefined}
                  aria-describedby={message ? `${reasonId}-error` : undefined}
                  onChange={(e) => setCellReason(link, cell, e.target.value)}
                />
                {message ? (
                  <p
                    id={`${reasonId}-error`}
                    className="delpi-prc__field-error"
                    role="alert"
                  >
                    {message}
                  </p>
                ) : null}
              </label>
            );
          })}
        </fieldset>

      <p className="delpi-prc__muted delpi-prc__correction-summary">
        {summary.scalarFields} campo(s) da ficha · {summary.suppliers}{" "}
        fornecedor(es) · {summary.supplierAttributes} atributo(s)
        {summary.firstMissingReason
          ? ` — motivo pendente: ${summary.firstMissingReason}`
          : ""}
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Editor de correção — card do solicitante                            */
/* ------------------------------------------------------------------ */

/** FIX-12 — id do controle associado a um targetKey no editor de
 * correção: ``field|path`` → justificativa do campo;
 * ``supplier|code|store|attr`` → input da célula; ``suppliers`` →
 * justificativa do grupo. */
/** FIX-12/AC-09 — mapeia ``data.fields`` do envelope de erro da
 * Engineering API para targetKeys do editor. O backend nomeia os
 * campos por posição do change (``changes[i].path`` /
 * ``changes[i].proposedValue``) ou pelo path direto; o que não for
 * identificável volta em ``unmapped`` e permanece erro global. */
export function mapApiFieldsToCorrectionErrors(
  fields: Record<string, string> | null | undefined,
  changes: PrcReturnedFieldChange[],
): {
  targetErrors: PrcCorrectionTargetErrors;
  unmapped: Record<string, string>;
} {
  const targetErrors: PrcCorrectionTargetErrors = {};
  const unmapped: Record<string, string> = {};
  for (const [field, message] of Object.entries(fields || {})) {
    const idxMatch = field.match(/^changes\[(\d+)\]\.(.+)$/);
    if (idxMatch) {
      const change = changes[Number(idxMatch[1])];
      if (!change) {
        unmapped[field] = message;
        continue;
      }
      targetErrors[
        change.path === "suppliers"
          ? "suppliers"
          : correctionFieldTargetKey(change.path)
      ] = message;
      continue;
    }
    if (field === "suppliers" || field.startsWith("suppliers")) {
      targetErrors["suppliers"] = message;
      continue;
    }
    if (changes.some((c) => c.path === field)) {
      targetErrors[correctionFieldTargetKey(field)] = message;
      continue;
    }
    unmapped[field] = message;
  }
  return { targetErrors, unmapped };
}

export function returnedFieldControlId(
  idPrefix: string,
  targetKey: string,
): string {
  const [kind, ...rest] = targetKey.split("|");
  if (kind === "field") return `${idPrefix}-justify-${rest.join("|")}`;
  if (kind === "suppliers") return `${idPrefix}-justify-suppliers`;
  const [code, store, attr] = rest;
  return `${idPrefix}-sup-${code}-${store}-${attr}`;
}

export function PrcReturnedFieldsEditor({
  targets,
  fieldSpecs,
  draft,
  busy,
  idPrefix = "prc-correct",
  externalErrors,
  onSubmit,
  onCancel,
}: {
  targets: PrcCorrectionTargetWire[];
  fieldSpecs: PrcFieldSpecLike[];
  /** ``technical_data`` vigente — origem dos valores atuais. */
  draft: Record<string, unknown>;
  busy?: boolean;
  idPrefix?: string;
  /** FIX-12 — erros vindos do backend (``data.fields`` mapeados para
   * targetKeys pelo consumidor) exibidos junto ao campo. */
  externalErrors?: PrcCorrectionTargetErrors;
  onSubmit: (changes: PrcReturnedFieldChange[]) => void;
  onCancel?: () => void;
}) {
  const fieldTargets = useMemo(() => fieldTargetsOf(targets), [targets]);
  const supplierTargets = useMemo(() => hasSupplierTargets(targets), [targets]);
  const returnedAttrs = useMemo(
    () => returnedSupplierAttrMap(targets),
    [targets],
  );
  const supplierReasons = useMemo(
    () => returnedSupplierReasonMap(targets),
    [targets],
  );
  const specByPath = useMemo(
    () => new Map((fieldSpecs || []).map((s) => [s.path, s] as const)),
    [fieldSpecs],
  );
  const [values, setValues] = useState<Record<string, string>>(() => {
    const out: Record<string, string> = {};
    for (const t of fieldTargetsOf(targets)) {
      const p = String(t.targetPath || "");
      out[p] = scalarCurrent(draft, p);
    }
    return out;
  });
  const [justifications, setJustifications] = useState<
    Record<string, string>
  >({});
  const [supplierJustification, setSupplierJustification] = useState("");
  const [supplierRows, setSupplierRows] = useState<SupplierRow[]>(() =>
    toSupplierRows(draft.suppliers),
  );
  const [formError, setFormError] = useState("");
  /* FIX-12 — erros por alvo: validação local + erros externos (API)
   * mesclados, exibidos junto ao campo. */
  const [fieldErrors, setFieldErrors] = useState<PrcCorrectionTargetErrors>({});
  const mergedErrors = useMemo<PrcCorrectionTargetErrors>(
    () => ({ ...fieldErrors, ...(externalErrors || {}) }),
    [fieldErrors, externalErrors],
  );

  const clearTargetError = (key: string) => {
    setFieldErrors((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const supplierRowsChanged = useMemo(() => {
    const current = toSupplierRows(draft.suppliers);
    const byKey = new Map(
      current.map((r) => [prcSupplierLinkKey(r.supplierCode, r.store), r]),
    );
    return supplierRows.some((row) => {
      const base = byKey.get(prcSupplierLinkKey(row.supplierCode, row.store));
      if (!base) return false;
      return PRC_SUPPLIER_EDITABLE_ATTRIBUTES.some(
        (attr) => row[attr].trim() !== (base[attr] || "").trim(),
      );
    });
  }, [supplierRows, draft.suppliers]);

  const submit = () => {
    const { changes, error, errors } = buildReturnedChanges({
      targets,
      draft,
      supplierRows,
      fieldValues: values,
      justifications,
      supplierJustification,
    });
    if (!changes) {
      setFormError(error);
      setFieldErrors(errors);
      /* FIX-12 — foca o primeiro alvo inválido na ordem visual e
       * rola até ele dentro do card. */
      const ordered = [
        ...fieldTargets.map((t) =>
          correctionFieldTargetKey(String(t.targetPath || "")),
        ),
        ...supplierRows.flatMap((row) => {
          const link = {
            supplierCode: row.supplierCode,
            store: row.store,
          };
          return [
            correctionSupplierTargetKey(link, "partNumber"),
            correctionSupplierTargetKey(link, "catalogNumber"),
            correctionSupplierTargetKey(link, "link"),
          ];
        }),
        "suppliers",
      ];
      const first = firstInvalidCorrectionTarget(errors, ordered);
      if (first) {
        requestAnimationFrame(() => {
          const el = document.getElementById(
            returnedFieldControlId(idPrefix, first),
          );
          if (!el) return;
          el.scrollIntoView({ block: "center", behavior: "auto" });
          el.focus({ preventScroll: true });
        });
      }
      return;
    }
    setFormError("");
    setFieldErrors({});
    onSubmit(changes);
  };

  const reviewItems = useMemo(() => {
    const items: Array<{ label: string; before: string; after: string }> = [];
    for (const t of fieldTargets) {
      const path = String(t.targetPath || "");
      const before = scalarCurrent(draft, path) || "vazio";
      const after = (values[path] ?? "").trim();
      items.push({
        label: PRC_FIELD_LABELS[path] || path,
        before,
        after: after || "(mantido — confirmação)",
      });
    }
    if (supplierTargets) {
      const current = toSupplierRows(draft.suppliers);
      const byKey = new Map(
        current.map((r) => [
          prcSupplierLinkKey(r.supplierCode, r.store),
          r,
        ]),
      );
      for (const row of supplierRows) {
        const key = prcSupplierLinkKey(row.supplierCode, row.store);
        const base = byKey.get(key);
        const attrs = returnedAttrs.get(key);
        if (!base || !attrs) continue;
        for (const attr of PRC_SUPPLIER_EDITABLE_ATTRIBUTES) {
          if (!attrs.has(attr)) continue;
          items.push({
            label: `${PRC_SUPPLIER_LABELS[attr]} — ${row.supplierCode} / ${row.store}`,
            before: (base[attr] || "").trim() || "vazio",
            after: row[attr].trim() || "(mantido — confirmação)",
          });
        }
      }
    }
    return items;
  }, [fieldTargets, supplierTargets, supplierRows, values, draft, returnedAttrs]);

  return (
    <div className="delpi-prc__correction-editor">
      {fieldTargets.length ? (
        <fieldset className="delpi-prc__correction-group">
          <legend>Campos devolvidos</legend>
          {fieldTargets.map((t) => {
            const path = String(t.targetPath || "");
            const spec = specByPath.get(path);
            const label = PRC_FIELD_LABELS[path] || path;
            const current = scalarCurrent(draft, path);
            const value = values[path] ?? current;
            const dirty = value.trim() !== current.trim();
            return (
              <div key={path} className="delpi-prc__correction-field">
                <p className="delpi-prc__correction-reason-note">
                  <strong>{label}:</strong> {t.reason}
                </p>
                <p className="delpi-prc__muted">
                  Valor atual: {current || "—"}
                </p>
                {spec?.enumValues?.length ? (
                  <FormSelectControl
                    id={`${idPrefix}-field-${path}`}
                    ariaLabel={`Novo valor — ${label}`}
                    value={value}
                    disabled={busy}
                    options={spec.enumValues.map((v) => ({
                      value: v,
                      label: v,
                    }))}
                    onChange={(v) =>
                      setValues((s) => ({ ...s, [path]: v }))
                    }
                  />
                ) : (
                  <label className="delpi-prc__correction-reason">
                    <span className="delpi-prc__muted">
                      Novo valor — {label}
                    </span>
                    <input
                      id={`${idPrefix}-field-${path}`}
                      type="text"
                      value={value}
                      disabled={busy}
                      maxLength={spec?.maxLength}
                      onChange={(e) =>
                        setValues((s) => ({ ...s, [path]: e.target.value }))
                      }
                    />
                  </label>
                )}
                <label className="delpi-prc__correction-reason">
                  <span className="delpi-prc__muted">
                    {dirty
                      ? "Justificativa da correção"
                      : "Confirmação / justificativa (opcional)"}
                  </span>
                  {(() => {
                    const key = correctionFieldTargetKey(path);
                    const message = mergedErrors[key];
                    const inputId = `${idPrefix}-justify-${path}`;
                    return (
                      <>
                        <input
                          id={inputId}
                          type="text"
                          value={justifications[path] || ""}
                          disabled={busy}
                          maxLength={500}
                          aria-invalid={message ? true : undefined}
                          aria-describedby={
                            message ? `${inputId}-error` : undefined
                          }
                          onChange={(e) => {
                            setJustifications((s) => ({
                              ...s,
                              [path]: e.target.value,
                            }));
                            if (message) clearTargetError(key);
                          }}
                        />
                        {message ? (
                          <p
                            id={`${inputId}-error`}
                            className="delpi-prc__field-error"
                            role="alert"
                          >
                            {message}
                          </p>
                        ) : null}
                      </>
                    );
                  })()}
                </label>
              </div>
            );
          })}
        </fieldset>
      ) : null}

      {supplierTargets ? (
        <fieldset className="delpi-prc__correction-group">
          <legend>Fornecedores</legend>
          <div className="delpi-prc__supplier-table-wrap">
            <table className="delpi-prc__supplier-table delpi-prc__correction-table">
              <caption className="delpi-prc__sr-only">
                Atributos de fornecedores devolvidos para correção
              </caption>
              <thead>
                <tr>
                  <th scope="col">Código</th>
                  <th scope="col">Loja</th>
                  <th scope="col">Razão social</th>
                  <th scope="col">Nome fantasia</th>
                  <th scope="col">{PRC_SUPPLIER_LABELS.partNumber}</th>
                  <th scope="col">{PRC_SUPPLIER_LABELS.catalogNumber}</th>
                </tr>
              </thead>
              <tbody>
                {supplierRows.map((row) => {
                  const key = prcSupplierLinkKey(
                    row.supplierCode,
                    row.store,
                  );
                  const attrs = returnedAttrs.get(key);
                  const linkReason =
                    supplierReasons.get(`${key}|link`) || "";
                  const rowEditable = Boolean(attrs && attrs.size);
                  return (
                    <tr key={key} data-link-key={key}>
                      <td data-label="Código">{row.supplierCode}</td>
                      <td data-label="Loja">{row.store}</td>
                      <td data-label="Razão social">
                        {row.supplierName || "—"}
                        {linkReason ? (
                          <span className="delpi-prc__change-notes">
                            Correção solicitada — {linkReason}
                          </span>
                        ) : null}
                      </td>
                      <td data-label="Nome fantasia">
                        {row.supplierShortName || "—"}
                      </td>
                      {PRC_SUPPLIER_EDITABLE_ATTRIBUTES.map((attr) => {
                        const editable = rowEditable && attrs!.has(attr);
                        const attrReason =
                          supplierReasons.get(`${key}|${attr}`) || "";
                        return (
                          <td
                            key={attr}
                            data-label={PRC_SUPPLIER_LABELS[attr]}
                            className="delpi-prc__correction-cell"
                          >
                            {editable ? (
                              <>
                                {(() => {
                                  const targetKey =
                                    correctionSupplierTargetKey(
                                      {
                                        supplierCode: row.supplierCode,
                                        store: row.store,
                                      },
                                      attr,
                                    );
                                  const message = mergedErrors[targetKey];
                                  const inputId = `${idPrefix}-sup-${row.supplierCode}-${row.store}-${attr}`;
                                  return (
                                    <>
                                      <input
                                        id={inputId}
                                        type="text"
                                        className="delpi-prc__cell-input"
                                        aria-label={`${PRC_SUPPLIER_LABELS[attr]} — ${row.supplierCode} / ${row.store}`}
                                        value={row[attr]}
                                        disabled={busy}
                                        aria-invalid={
                                          message ? true : undefined
                                        }
                                        aria-describedby={
                                          message
                                            ? `${inputId}-error`
                                            : undefined
                                        }
                                        onChange={(e) => {
                                          setSupplierRows((rows) =>
                                            rows.map((r) =>
                                              r.rowId === row.rowId
                                                ? {
                                                    ...r,
                                                    [attr]:
                                                      e.target.value,
                                                  }
                                                : r,
                                            ),
                                          );
                                          if (message) {
                                            clearTargetError(targetKey);
                                          }
                                        }}
                                      />
                                      {message ? (
                                        <p
                                          id={`${inputId}-error`}
                                          className="delpi-prc__cell-error"
                                          role="alert"
                                        >
                                          {message}
                                        </p>
                                      ) : null}
                                    </>
                                  );
                                })()}
                                {attrReason ? (
                                  <span className="delpi-prc__change-notes">
                                    Correção solicitada — {attrReason}
                                  </span>
                                ) : null}
                              </>
                            ) : (
                              <span className="delpi-prc__muted">
                                {row[attr] || "—"}
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {supplierRowsChanged ? (
            <label className="delpi-prc__correction-reason">
              <span className="delpi-prc__muted">
                Justificativa da correção dos fornecedores
              </span>
              {(() => {
                const message = mergedErrors["suppliers"];
                const inputId = `${idPrefix}-justify-suppliers`;
                return (
                  <>
                    <input
                      id={inputId}
                      type="text"
                      value={supplierJustification}
                      disabled={busy}
                      maxLength={500}
                      aria-invalid={message ? true : undefined}
                      aria-describedby={
                        message ? `${inputId}-error` : undefined
                      }
                      onChange={(e) => {
                        setSupplierJustification(e.target.value);
                        if (message) clearTargetError("suppliers");
                      }}
                    />
                    {message ? (
                      <p
                        id={`${inputId}-error`}
                        className="delpi-prc__field-error"
                        role="alert"
                      >
                        {message}
                      </p>
                    ) : null}
                  </>
                );
              })()}
            </label>
          ) : null}
        </fieldset>
      ) : null}

      <fieldset className="delpi-prc__correction-group">
        <legend>Resumo antes do reenvio</legend>
        <ul className="delpi-prc__correction-review">
          {reviewItems.map((item) => (
            <li key={item.label}>
              <strong>{item.label}</strong>: {item.before} → {item.after}
            </li>
          ))}
        </ul>
      </fieldset>

      {formError ? (
        <p className="delpi-prc__field-error" role="alert">
          {formError}
        </p>
      ) : null}
      <div className="delpi-prc__correction-actions">
        {onCancel ? (
          <ActionButton variant="ghost" disabled={busy} onClick={onCancel}>
            Cancelar
          </ActionButton>
        ) : null}
        <ActionButton variant="primary" disabled={busy} onClick={submit}>
          Salvar correções e reenviar
        </ActionButton>
      </div>
    </div>
  );
}
