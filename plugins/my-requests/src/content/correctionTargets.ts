/** Catálogo de campos/seções marcáveis na devolução — espelha requests-api. */

export type CorrectionTargetOption = {
  id: string;
  label: string;
  /** Wizard step id quando aplicável (invoice). */
  wizardStepId?: string;
};

const INVOICE_TARGETS: CorrectionTargetOption[] = [
  { id: "recipient", label: "Destinatário", wizardStepId: "recipient" },
  { id: "invoice_type", label: "Tipo de NF", wizardStepId: "invoiceType" },
  { id: "items", label: "Itens", wizardStepId: "items" },
  { id: "freight", label: "Transporte", wizardStepId: "freight" },
  { id: "extras", label: "Adicionais (peso, volumes, observação)", wizardStepId: "extras" },
];

const RAW_MATERIAL_TARGETS: CorrectionTargetOption[] = [
  { id: "description", label: "Descrição" },
  { id: "unit", label: "Unidade" },
  { id: "notes", label: "Observações" },
];

const BY_TYPE: Record<string, CorrectionTargetOption[]> = {
  "invoice-issuance": INVOICE_TARGETS,
  "raw-material-creation": RAW_MATERIAL_TARGETS,
};

export function correctionTargetOptionsForType(
  typeCode: string | null | undefined,
): CorrectionTargetOption[] {
  if (!typeCode) return [];
  return BY_TYPE[typeCode] ?? [];
}

export function correctionTargetLabel(
  typeCode: string | null | undefined,
  targetId: string,
): string {
  const hit = correctionTargetOptionsForType(typeCode).find((row) => row.id === targetId);
  return hit?.label ?? targetId;
}

export function correctionTargetLabels(
  typeCode: string | null | undefined,
  targetIds: string[] | null | undefined,
): string[] {
  if (!targetIds?.length) return [];
  return targetIds.map((id) => correctionTargetLabel(typeCode, id));
}

/** Map API correction target ids → wizard step ids (invoice). */
export function wizardStepIdsForCorrectionTargets(
  targetIds: string[] | null | undefined,
): string[] {
  if (!targetIds?.length) return [];
  const map = new Map(
    INVOICE_TARGETS.filter((row) => row.wizardStepId).map((row) => [
      row.id,
      row.wizardStepId as string,
    ]),
  );
  const out: string[] = [];
  const seen = new Set<string>();
  for (const id of targetIds) {
    const step = map.get(id);
    if (!step || seen.has(step)) continue;
    seen.add(step);
    out.push(step);
  }
  return out;
}
