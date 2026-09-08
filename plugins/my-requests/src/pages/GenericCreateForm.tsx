import { useState, type FormEvent } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { createRequest } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  branchCodeForCreate,
  requiresBranchField,
  showsBranchField,
} from "../domain/branchScope";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../types/requests";
import {
  MyRequestsFormActions,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SelectField,
} from "../ui/mrUi";

type GenericCreateFormProps = {
  requestType: RequestTypeSummary;
  onCancel: () => void;
};

/** Create flow for types that are neither specialized nor schema_driven. */
export function GenericCreateForm({ requestType, onCancel }: GenericCreateFormProps) {
  const access = useRequestsPermissions();
  const branchOptions = (access.branches.length ? access.branches : ["01", "02"]).map(
    (code) => ({ value: code, label: code }),
  );
  const showBranch = showsBranchField(requestType.branch_scope);
  const [branchCode, setBranchCode] = useState(branchOptions[0]?.value || "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (requiresBranchField(requestType.branch_scope) && !branchCode.trim()) {
      setError("Selecione a filial.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await createRequest({
        typeCode: requestType.code,
        branchCode: branchCodeForCreate(requestType.branch_scope, branchCode),
        idempotencyKey: crypto.randomUUID(),
        payload: {},
      });
      navigateMyRequestsPath(myRequestsPath({ requestId: created.id }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a solicitação.");
      setBusy(false);
    }
  }

  return (
    <AppShell title={requestType.name} canCreate>
      <MyRequestsSectionCard title="Criar solicitação">
        <div data-help="new" title={MY_REQUESTS_HELP_TOOLTIPS.new.section}>
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          <form className="my-requests-form-stack" onSubmit={onSubmit}>
            {showBranch ? (
              <SelectField
                label="Filial"
                hint={MY_REQUESTS_HELP_TOOLTIPS.new.branch}
                value={branchCode}
                onChange={setBranchCode}
                options={branchOptions}
                disabled={busy}
              />
            ) : null}
            <MyRequestsFormActions>
              <ActionButton type="button" variant="ghost" onClick={onCancel} disabled={busy}>
                Voltar
              </ActionButton>
              <ActionButton type="submit" variant="primary" disabled={busy}>
                Criar
              </ActionButton>
            </MyRequestsFormActions>
          </form>
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
