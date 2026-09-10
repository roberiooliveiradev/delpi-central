import { useEffect, useState, type FormEvent } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { createRequest, patchRequestPayload } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { AttachmentsPanel } from "../components/AttachmentsPanel";
import {
  revokeStagedPreviews,
  StagedAttachmentsField,
  type StagedAttachment,
} from "../components/StagedAttachmentsField";
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
import { uploadStagedAttachments } from "../utils/uploadStagedAttachments";

type GenericCreateFormProps = {
  requestType: RequestTypeSummary;
  onCancel: () => void;
  mode?: "create" | "edit";
  requestId?: string;
  initialPayload?: Record<string, unknown>;
  initialVersion?: number;
};

/** Create/edit flow for types that are neither specialized nor schema_driven. */
export function GenericCreateForm({
  requestType,
  onCancel,
  mode = "create",
  requestId,
  initialVersion,
}: GenericCreateFormProps) {
  const isEdit = mode === "edit";
  const access = useRequestsPermissions();
  const branchOptions = (access.branches.length ? access.branches : ["01", "02"]).map(
    (code) => ({ value: code, label: code }),
  );
  const showBranch = showsBranchField(requestType.branch_scope);
  const [branchCode, setBranchCode] = useState(branchOptions[0]?.value || "");
  const [stagedAttachments, setStagedAttachments] = useState<StagedAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(initialVersion ?? 1);

  useEffect(() => {
    return () => revokeStagedPreviews(stagedAttachments);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (requiresBranchField(requestType.branch_scope) && !branchCode.trim()) {
      setError("Selecione a filial.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      let targetId = requestId || "";
      if (isEdit) {
        if (!requestId) {
          setError("Solicitação inválida para edição.");
          setBusy(false);
          return;
        }
        const updated = await patchRequestPayload(requestId, {}, {
          version,
          idempotencyKey: crypto.randomUUID(),
        });
        setVersion(updated.version);
        targetId = updated.id;
      } else {
        const created = await createRequest({
          typeCode: requestType.code,
          branchCode: branchCodeForCreate(requestType.branch_scope, branchCode),
          idempotencyKey: crypto.randomUUID(),
          payload: {},
        });
        targetId = created.id;
      }

      if (!isEdit && stagedAttachments.length > 0) {
        const result = await uploadStagedAttachments(
          targetId,
          stagedAttachments.map((row) => row.file),
        );
        revokeStagedPreviews(stagedAttachments);
        setStagedAttachments([]);
        if (result.failed > 0) {
          setError(
            `Solicitação salva, mas ${result.failed} documento(s) não foram enviados.`,
          );
          navigateMyRequestsPath(myRequestsPath({ requestId: targetId }));
          return;
        }
      }

      navigateMyRequestsPath(myRequestsPath({ requestId: targetId }));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : isEdit
            ? "Não foi possível atualizar a solicitação."
            : "Não foi possível criar a solicitação.",
      );
      setBusy(false);
    }
  }

  return (
    <AppShell title={isEdit ? `Corrigir: ${requestType.name}` : requestType.name}>
      <MyRequestsSectionCard title={isEdit ? "Corrigir solicitação" : "Criar solicitação"}>
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
                disabled={busy || isEdit}
              />
            ) : null}
            {isEdit && requestId ? (
              <AttachmentsPanel requestId={requestId} canUpload />
            ) : (
              <StagedAttachmentsField
                items={stagedAttachments}
                onChange={setStagedAttachments}
                busy={busy}
              />
            )}
            <MyRequestsFormActions>
              <ActionButton type="button" variant="ghost" onClick={onCancel} disabled={busy}>
                Voltar
              </ActionButton>
              <ActionButton type="submit" variant="primary" disabled={busy}>
                {isEdit ? "Salvar correção" : "Criar"}
              </ActionButton>
            </MyRequestsFormActions>
          </form>
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
