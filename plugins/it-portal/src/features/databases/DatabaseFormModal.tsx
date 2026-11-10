import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { itPortalApi, type DatabaseInstance, type DatabaseInstanceInput } from "../../api/itPortalApi";
import { FormErrors } from "../../app/FormErrors";
import { ItpActionButton, ItpSelectField, ItpTextAreaField, ItpTextField, ItpWideDialog } from "../../app/itPortalUi";
import { toApiError, usePortal } from "../../app/PortalContext";
import {
  ADMINISTRATIVE_STATUS_OPTIONS,
  CRITICALITY_OPTIONS,
  DATABASE_FIELD_LABELS,
  DBMS_OPTIONS,
  ENVIRONMENT_OPTIONS,
  SECRET_WARNING,
} from "../../content/labels";
import { ResourcePicker } from "../inventory/ResourcePicker";
import { useInvalidateInventory } from "../servers/ServerFormModal";

const EMPTY_FORM: DatabaseInstanceInput = {
  name: "",
  dbms: "",
  version: "",
  server_id: "",
  port: "",
  environment: "",
  purpose: "",
  criticality: "",
  responsible: "",
  administrative_status: "in_operation",
  technical_notes: "",
};

function toForm(database: DatabaseInstance): DatabaseInstanceInput {
  return {
    name: database.name,
    dbms: database.dbms,
    version: database.version ?? "",
    server_id: database.server_id,
    port: database.port === null ? "" : String(database.port),
    environment: database.environment,
    purpose: database.purpose ?? "",
    criticality: database.criticality,
    responsible: database.responsible,
    administrative_status: database.administrative_status,
    technical_notes: database.technical_notes ?? "",
  };
}

export function DatabaseFormModal({
  database,
  presetServerId,
  onClose,
  onSaved,
}: {
  database?: DatabaseInstance | null;
  presetServerId?: string;
  onClose: () => void;
  onSaved?: (database: DatabaseInstance) => void;
}) {
  const { notifySuccess } = usePortal();
  const invalidate = useInvalidateInventory();
  const [form, setForm] = useState<DatabaseInstanceInput>(() =>
    database ? toForm(database) : { ...EMPTY_FORM, server_id: presetServerId ?? "" },
  );
  const editing = Boolean(database);

  const mutation = useMutation({
    mutationFn: (input: DatabaseInstanceInput) =>
      database
        ? itPortalApi.updateDatabase(database.id, input, database.revision)
        : itPortalApi.createDatabase(input),
    onSuccess: (saved) => {
      invalidate();
      notifySuccess(editing ? "Cadastro da instância atualizado." : `Instância ${saved.code} cadastrada.`);
      onSaved?.(saved);
      onClose();
    },
  });

  const set = (field: keyof DatabaseInstanceInput) => (value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));
  const submit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate(form);
  };

  return (
    <ItpWideDialog
      open
      title={editing ? `Editar ${database?.code}` : "Cadastrar instância de banco"}
      description="Inventário descritivo: nunca informe usuários, senhas, tokens ou strings de conexão. O nome é único por servidor."
      onClose={onClose}
      footer={
        <div className="itp-form-actions">
          <ItpActionButton variant="ghost" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </ItpActionButton>
          <ItpActionButton variant="primary" type="submit" form="itp-database-form" disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando…" : editing ? "Salvar alterações" : "Cadastrar"}
          </ItpActionButton>
        </div>
      }
    >
      <form id="itp-database-form" className="itp-form" onSubmit={submit} noValidate>
        <FormErrors error={mutation.error ? toApiError(mutation.error) : null} fieldLabels={DATABASE_FIELD_LABELS} />
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Identificação</legend>
          <ItpTextField
            label={DATABASE_FIELD_LABELS.name}
            hint="Nome da instância ou do banco. Ex.: ERP_PROD."
            value={form.name}
            onChange={set("name")}
            required
          />
          <ItpSelectField label={DATABASE_FIELD_LABELS.dbms} options={DBMS_OPTIONS} value={form.dbms} onChange={set("dbms")} required />
          <ItpTextField label={DATABASE_FIELD_LABELS.version} hint="Opcional. Ex.: 2019, 16.4." value={form.version} onChange={set("version")} />
          <ItpTextField
            label={DATABASE_FIELD_LABELS.port}
            hint="Opcional. Porta de escuta (1–65535)."
            value={form.port}
            onChange={set("port")}
          />
          <ItpSelectField
            label={DATABASE_FIELD_LABELS.environment}
            options={ENVIRONMENT_OPTIONS}
            value={form.environment}
            onChange={set("environment")}
            required
          />
          <ItpTextField label={DATABASE_FIELD_LABELS.purpose} value={form.purpose} onChange={set("purpose")} />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">{DATABASE_FIELD_LABELS.server_id}</legend>
          <ResourcePicker
            kind="server"
            value={form.server_id}
            onChange={set("server_id")}
            initialOption={
              database
                ? {
                    value: database.server_id,
                    label: `${database.server.code} · ${database.server.name} (${database.server.hostname})`,
                  }
                : undefined
            }
          />
        </fieldset>
        <fieldset className="itp-form-grid">
          <legend className="itp-form-legend">Operação e responsabilidade</legend>
          <ItpSelectField
            label={DATABASE_FIELD_LABELS.criticality}
            options={CRITICALITY_OPTIONS}
            value={form.criticality}
            onChange={set("criticality")}
            required
          />
          <ItpSelectField
            label={DATABASE_FIELD_LABELS.administrative_status}
            hint="Situação informada manualmente — não é monitoramento."
            options={ADMINISTRATIVE_STATUS_OPTIONS}
            value={form.administrative_status}
            onChange={set("administrative_status")}
            required
          />
          <ItpTextField
            label={DATABASE_FIELD_LABELS.responsible}
            hint="Pessoa ou equipe responsável."
            value={form.responsible}
            onChange={set("responsible")}
            required
          />
        </fieldset>
        <ItpTextAreaField
          label={DATABASE_FIELD_LABELS.technical_notes}
          hint={SECRET_WARNING}
          value={form.technical_notes}
          onChange={set("technical_notes")}
          rows={4}
          maxLength={4000}
          fullWidth
        />
      </form>
    </ItpWideDialog>
  );
}
