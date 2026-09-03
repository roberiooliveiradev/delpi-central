import { useEffect, useState, type FormEvent } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { createRequest, listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { InvoiceIssuanceWizard } from "../features/invoice-issuance/ui/InvoiceIssuanceWizard";
import { SchemaFormPage } from "../features/raw-material-creation/SchemaFormPage";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../types/requests";
import {
  MyRequestsFormActions,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SelectField,
} from "../ui/mrUi";
import { readTypeCodeFromSearch } from "./newRequestDeepLink";

export function NewRequestPage() {
  const access = useRequestsPermissions();
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [typeCode, setTypeCode] = useState(() => readTypeCodeFromSearch());
  const [branchCode, setBranchCode] = useState(access.branches[0] || "01");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [specializedOpen, setSpecializedOpen] = useState(false);

  const selectedType = types.find((item) => item.code === typeCode) || null;

  useEffect(() => {
    const ac = new AbortController();
    const preferred = readTypeCodeFromSearch();
    listRequestTypes({ signal: ac.signal })
      .then((items) => {
        setTypes(items);
        if (preferred && items.some((item) => item.code === preferred)) {
          setTypeCode(preferred);
          return;
        }
        if (!preferred && items[0]?.code) setTypeCode(items[0].code);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  if (specializedOpen && selectedType?.code === "invoice-issuance") {
    return (
      <InvoiceIssuanceWizard
        lockedBranch={branchCode}
        onCancel={() => setSpecializedOpen(false)}
      />
    );
  }

  if (specializedOpen && selectedType?.code === "raw-material-creation") {
    return (
      <SchemaFormPage
        requestType={selectedType}
        lockedBranch={branchCode || undefined}
        onCancel={() => setSpecializedOpen(false)}
      />
    );
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!typeCode || !selectedType) return;
    if (
      selectedType.presentation_mode === "specialized" ||
      selectedType.presentation_mode === "schema_driven" ||
      typeCode === "invoice-issuance" ||
      typeCode === "raw-material-creation"
    ) {
      setSpecializedOpen(true);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await createRequest({
        typeCode,
        branchCode,
        idempotencyKey: crypto.randomUUID(),
        payload: {},
      });
      window.location.assign(`/apps/my-requests/requests/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar");
      setBusy(false);
    }
  }

  const branchOptions = (access.branches.length ? access.branches : ["01", "02"]).map(
    (code) => ({ value: code, label: code }),
  );
  const typeOptions = types.map((item) => ({
    value: item.code,
    label: `${item.name} (${item.code})`,
  }));

  const submitLabel =
    typeCode === "invoice-issuance"
      ? "Abrir wizard de NF"
      : typeCode === "raw-material-creation"
        ? "Abrir formulário de MP"
        : "Criar";

  return (
    <AppShell title="Nova solicitação" canCreate>
      <MyRequestsSectionCard title="Criar">
        <div data-help="new" title={MY_REQUESTS_HELP_TOOLTIPS.new.section}>
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          <form className="my-requests-form-stack" onSubmit={onSubmit}>
            <SelectField
              label="Tipo"
              hint={MY_REQUESTS_HELP_TOOLTIPS.new.type}
              value={typeCode}
              onChange={setTypeCode}
              options={typeOptions}
              disabled={busy || types.length === 0}
            />
            <SelectField
              label="Filial"
              hint={MY_REQUESTS_HELP_TOOLTIPS.new.branch}
              value={branchCode}
              onChange={setBranchCode}
              options={branchOptions}
              disabled={busy}
            />
            <MyRequestsFormActions>
              <ActionButton type="submit" variant="primary" disabled={busy || !typeCode}>
                {submitLabel}
              </ActionButton>
            </MyRequestsFormActions>
          </form>
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
