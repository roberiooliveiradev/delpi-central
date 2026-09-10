import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ActionButton, FieldLabel, NativeTextAreaControl } from "@delpi/plugin-ui/index";

import { createRequest, patchRequestPayload } from "../../api/requestsApi";
import { AppShell } from "../../components/AppShell";
import { AttachmentsPanel } from "../../components/AttachmentsPanel";
import {
  revokeStagedPreviews,
  StagedAttachmentsField,
  type StagedAttachment,
} from "../../components/StagedAttachmentsField";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  branchCodeForCreate,
  requiresBranchField,
  showsBranchField,
} from "../../domain/branchScope";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../../hooks/myRequestsNavigation";
import { useRequestsPermissions } from "../../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../../types/requests";
import {
  MyRequestsFormActions,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SelectField,
  TextField,
} from "../../ui/mrUi";
import {
  emptyValuesFromFields,
  mapFormSchemaToFields,
  type FormSchema,
  type UiSchema,
} from "./mapFormSchemaToFields";
import { uploadStagedAttachments } from "../../utils/uploadStagedAttachments";

type SchemaFormPageProps = {
  requestType: RequestTypeSummary;
  /** @deprecated Prefer branch_scope on requestType */
  lockedBranch?: string;
  onCancel?: () => void;
  mode?: "create" | "edit";
  requestId?: string;
  initialPayload?: Record<string, unknown>;
  initialVersion?: number;
};

export function SchemaFormPage({
  requestType,
  lockedBranch,
  onCancel,
  mode = "create",
  requestId,
  initialPayload,
  initialVersion,
}: SchemaFormPageProps) {
  const isEdit = mode === "edit";
  const access = useRequestsPermissions();
  const branchOptions = (access.branches.length ? access.branches : ["01", "02"]).map(
    (code) => ({ value: code, label: code }),
  );
  const showBranch = showsBranchField(requestType.branch_scope);
  const [branchCode, setBranchCode] = useState(
    lockedBranch || branchOptions[0]?.value || "",
  );
  const fields = useMemo(
    () =>
      mapFormSchemaToFields(
        (requestType.form_schema || {}) as FormSchema,
        (requestType.ui_schema || {}) as UiSchema,
      ),
    [requestType.code, requestType.form_schema, requestType.ui_schema],
  );
  const [values, setValues] = useState<Record<string, string>>(() => {
    const empty = emptyValuesFromFields(fields);
    if (!isEdit || !initialPayload) return empty;
    const next = { ...empty };
    for (const field of fields) {
      const raw = initialPayload[field.name];
      next[field.name] = raw == null ? "" : String(raw);
    }
    return next;
  });
  const [stagedAttachments, setStagedAttachments] = useState<StagedAttachment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(initialVersion ?? 1);

  useEffect(() => {
    if (isEdit) return;
    setValues(emptyValuesFromFields(fields));
  }, [fields, isEdit]);

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
      const payload: Record<string, unknown> = {};
      for (const field of fields) {
        payload[field.name] = values[field.name] ?? "";
      }
      let targetId = requestId || "";
      if (isEdit) {
        if (!requestId) {
          setError("Solicitação inválida para edição.");
          setBusy(false);
          return;
        }
        const updated = await patchRequestPayload(requestId, payload, {
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
          payload,
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

  if (!fields.length) {
    return (
      <AppShell title={requestType.name}>
        <MyRequestsSectionCard title="Formulário">
          <MyRequestsLoadingState message="Este tipo ainda não tem formulário configurado. Fale com o administrador." />
          {onCancel ? (
            <MyRequestsFormActions>
              <ActionButton type="button" variant="ghost" onClick={onCancel}>
                Voltar
              </ActionButton>
            </MyRequestsFormActions>
          ) : null}
        </MyRequestsSectionCard>
      </AppShell>
    );
  }

  return (
    <AppShell title={isEdit ? `Corrigir: ${requestType.name}` : requestType.name}>
      <MyRequestsSectionCard title={isEdit ? "Corrigir formulário" : "Formulário"}>
        <div data-help="raw-material-form" title={MY_REQUESTS_HELP_TOOLTIPS.rawMaterialForm.section}>
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
            {fields.map((field) => {
              if (field.kind === "select") {
                return (
                  <SelectField
                    key={field.name}
                    label={field.label}
                    hint={field.hint}
                    value={values[field.name] || ""}
                    onChange={(value) =>
                      setValues((prev) => ({ ...prev, [field.name]: value }))
                    }
                    options={field.options || []}
                    disabled={busy}
                  />
                );
              }
              if (field.kind === "textarea") {
                const id = `mr-schema-${field.name}`;
                return (
                  <div key={field.name}>
                    <FieldLabel label={field.label} htmlFor={id} hint={field.hint} />
                    <NativeTextAreaControl
                      id={id}
                      value={values[field.name] || ""}
                      onChange={(value) =>
                        setValues((prev) => ({ ...prev, [field.name]: value }))
                      }
                      rows={3}
                      disabled={busy}
                    />
                  </div>
                );
              }
              return (
                <TextField
                  key={field.name}
                  label={field.label}
                  hint={field.hint}
                  value={values[field.name] || ""}
                  onChange={(value) =>
                    setValues((prev) => ({ ...prev, [field.name]: value }))
                  }
                  disabled={busy}
                />
              );
            })}
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
              {onCancel ? (
                <ActionButton type="button" variant="ghost" onClick={onCancel} disabled={busy}>
                  Voltar
                </ActionButton>
              ) : null}
              <ActionButton type="submit" variant="primary" disabled={busy}>
                {isEdit ? "Salvar correção" : "Criar solicitação"}
              </ActionButton>
            </MyRequestsFormActions>
          </form>
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
