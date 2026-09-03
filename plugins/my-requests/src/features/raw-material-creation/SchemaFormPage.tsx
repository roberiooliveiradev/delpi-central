import { useEffect, useMemo, useState, type FormEvent } from "react";
import { ActionButton, FieldLabel, NativeTextAreaControl } from "@delpi/plugin-ui/index";

import { createRequest } from "../../api/requestsApi";
import { AppShell } from "../../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../../content/helpTooltips";
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

type SchemaFormPageProps = {
  requestType: RequestTypeSummary;
  lockedBranch?: string;
  onCancel?: () => void;
};

export function SchemaFormPage({ requestType, lockedBranch, onCancel }: SchemaFormPageProps) {
  const fields = useMemo(
    () =>
      mapFormSchemaToFields(
        (requestType.form_schema || {}) as FormSchema,
        (requestType.ui_schema || {}) as UiSchema,
      ),
    [requestType.code, requestType.form_schema, requestType.ui_schema],
  );
  const [values, setValues] = useState<Record<string, string>>(() => emptyValuesFromFields(fields));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setValues(emptyValuesFromFields(fields));
  }, [fields]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {};
      for (const field of fields) {
        payload[field.name] = values[field.name] ?? "";
      }
      const created = await createRequest({
        typeCode: requestType.code,
        branchCode: lockedBranch,
        idempotencyKey: crypto.randomUUID(),
        payload,
      });
      window.location.assign(`/apps/my-requests/requests/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar");
      setBusy(false);
    }
  }

  if (!fields.length) {
    return (
      <AppShell title={requestType.name} canCreate>
        <MyRequestsSectionCard title="Formulário">
          <MyRequestsLoadingState message="Tipo sem form_schema configurado." />
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
    <AppShell title={requestType.name} canCreate>
      <MyRequestsSectionCard title="Formulário">
        <div data-help="raw-material-form" title={MY_REQUESTS_HELP_TOOLTIPS.rawMaterialForm.section}>
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          <form className="my-requests-form-stack" onSubmit={onSubmit}>
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
            <MyRequestsFormActions>
              {onCancel ? (
                <ActionButton type="button" variant="ghost" onClick={onCancel} disabled={busy}>
                  Voltar
                </ActionButton>
              ) : null}
              <ActionButton type="submit" variant="primary" disabled={busy}>
                Criar solicitação
              </ActionButton>
            </MyRequestsFormActions>
          </form>
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
