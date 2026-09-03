import { useEffect, useState, type FormEvent } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { createRequest, listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { InvoiceIssuanceWizard } from "../features/invoice-issuance/ui/InvoiceIssuanceWizard";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../types/requests";
import {
  MyRequestsFormActions,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SelectField,
} from "../ui/mrUi";

export function NewRequestPage() {
  const access = useRequestsPermissions();
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [typeCode, setTypeCode] = useState("");
  const [branchCode, setBranchCode] = useState(access.branches[0] || "01");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [wizardOpen, setWizardOpen] = useState(false);

  useEffect(() => {
    const ac = new AbortController();
    listRequestTypes({ signal: ac.signal })
      .then((items) => {
        setTypes(items);
        if (items[0]?.code) setTypeCode(items[0].code);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  if (wizardOpen && typeCode === "invoice-issuance") {
    return (
      <InvoiceIssuanceWizard
        lockedBranch={branchCode}
        onCancel={() => setWizardOpen(false)}
      />
    );
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!typeCode) return;
    if (typeCode === "invoice-issuance") {
      setWizardOpen(true);
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
              <ActionButton
                type="submit"
                variant="primary"
                disabled={busy || !typeCode}
              >
                {typeCode === "invoice-issuance" ? "Abrir wizard de NF" : "Criar"}
              </ActionButton>
            </MyRequestsFormActions>
          </form>
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
