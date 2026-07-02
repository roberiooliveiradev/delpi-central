import type {
  Certificate,
  CertificateFormState,
  CertificateItem,
  CertificateSavePayload,
  CertificateSampleType,
  ChecklistTemplateItem,
  OpLookup,
} from "../types/qualityLabels";

export function certificateToForm(cert: Certificate): CertificateFormState {
  return {
    sampleType: cert.sampleType ?? "fornecimento",
    quantity: cert.quantity ?? "",
    sampleQuantity: cert.sampleQuantity ?? "",
    customerName: cert.customerName ?? "",
    customerCode: cert.customerCode ?? "",
    customerStore: cert.customerStore ?? "",
    customerItem: cert.customerItem ?? "",
    customerItemRev: cert.customerItemRev ?? "",
    customerSource: cert.customerSource ?? "manual",
    delpiNotes: cert.delpiNotes ?? "",
    customerNotes: cert.customerNotes ?? "",
    items: cert.items ?? [],
  };
}

export function formToSavePayload(
  form: CertificateFormState,
  issue: boolean,
): CertificateSavePayload {
  return {
    sampleType: form.sampleType,
    quantity: form.quantity.trim() || null,
    sampleQuantity: form.sampleQuantity.trim() || null,
    customerCode: form.customerCode.trim() || null,
    customerStore: form.customerStore.trim() || null,
    customerName: form.customerName.trim() || null,
    customerItem: form.customerItem.trim() || null,
    customerItemRev: form.customerItemRev.trim() || null,
    customerSource: form.customerSource,
    delpiNotes: form.delpiNotes.trim() || null,
    customerNotes: form.customerNotes.trim() || null,
    items: form.items
      .filter((item) => item.description.trim().length > 0)
      .map((item, index) => ({
        position: index + 1,
        description: item.description.trim(),
        status: item.status,
        isCustom: item.isCustom,
      })),
    issue,
  };
}

export function buildEmptyDraft(options: {
  templateItems: ChecklistTemplateItem[];
  inspectedQuantity?: string;
  lookup?: OpLookup | null;
}): CertificateFormState {
  const inspected = options.inspectedQuantity?.trim();
  const sampleQuantity = inspected ? `${inspected} peças` : "";
  const customer = options.lookup?.customer;

  const items: CertificateItem[] = options.templateItems.map((item) => ({
    position: item.position,
    description: item.description,
    status: "A",
    isCustom: false,
  }));

  return {
    sampleType: "fornecimento",
    quantity: "",
    sampleQuantity,
    customerName: customer?.name ?? "",
    customerCode: customer?.code ?? "",
    customerStore: customer?.store ?? "",
    customerItem: "",
    customerItemRev: "",
    customerSource: customer?.source ?? "manual",
    delpiNotes: "",
    customerNotes: "",
    items,
  };
}

export function syncDraftFromInspection(
  draft: CertificateFormState,
  options: {
    inspectedQuantity?: string;
    lookup?: OpLookup | null;
  },
): CertificateFormState {
  const next = { ...draft, items: [...draft.items] };
  const inspected = options.inspectedQuantity?.trim();
  if (inspected && !next.sampleQuantity.trim()) {
    next.sampleQuantity = `${inspected} peças`;
  }

  const customer = options.lookup?.customer;
  if (customer?.name && !next.customerName.trim()) {
    next.customerName = customer.name;
    next.customerCode = customer.code ?? "";
    next.customerStore = customer.store ?? "";
    next.customerSource = customer.source;
  }

  return next;
}

export function hasCertificateContent(form: CertificateFormState): boolean {
  const hasCustomer = [
    form.customerName,
    form.customerCode,
    form.customerItem,
    form.quantity,
    form.delpiNotes,
    form.customerNotes,
  ].some((value) => value.trim().length > 0);

  const hasCustomItems = form.items.some(
    (item) => item.isCustom && item.description.trim().length > 0,
  );

  const hasNonDefaultStatus = form.items.some((item) => item.status !== "A");

  return hasCustomer || hasCustomItems || hasNonDefaultStatus || form.sampleType !== "fornecimento";
}

export const SAMPLE_OPTIONS: { value: CertificateSampleType; label: string }[] = [
  { value: "amostra", label: "Amostra" },
  { value: "lote_piloto", label: "Lote Piloto" },
  { value: "fornecimento", label: "Fornecimento" },
];
