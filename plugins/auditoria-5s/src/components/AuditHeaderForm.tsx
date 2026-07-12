import type { AuditArea } from "../api/audit5sApi";
import { NativeTextControl } from "@delpi/plugin-ui/index";
import { SHIFTS } from "../constants/audit5s";
import type { AuditAuditorSelection } from "../types/auditAuditor";
import { AuditAuditorPicker } from "./AuditAuditorPicker";
import { AuditResponsiblePicker } from "./AuditResponsiblePicker";
import { AuditNativeSelectField, AuditNativeTextField } from "./auditFormFields";

export type AuditHeaderFormValues = {
  audit_date: string;
  area_id: string;
  area_responsible: string;
  shift: string;
};

type Props = {
  title: string;
  areas: AuditArea[];
  form: AuditHeaderFormValues;
  onFormChange: (patch: Partial<AuditHeaderFormValues>) => void;
  selectedAuditors: AuditAuditorSelection[];
  onAuditorsChange: (auditors: AuditAuditorSelection[]) => void;
  newAreaName: string;
  onNewAreaNameChange: (value: string) => void;
  onCreateArea: () => void | Promise<void>;
  submitLabel: string;
  loading?: boolean;
  onSubmit: () => void | Promise<void>;
};

export function AuditHeaderForm({
  title,
  areas,
  form,
  onFormChange,
  selectedAuditors,
  onAuditorsChange,
  newAreaName,
  onNewAreaNameChange,
  onCreateArea,
  submitLabel,
  loading = false,
  onSubmit,
}: Props) {
  const canSubmit =
    Boolean(form.area_id) && Boolean(form.area_responsible.trim()) && selectedAuditors.length > 0;

  return (
    <section className="a5s-panel a5s-form a5s-form--new-audit">
      <h2 className="a5s-form__title">{title}</h2>
      <AuditNativeTextField
        id="a5s-audit-date"
        label="Data"
        type="date"
        value={form.audit_date}
        onChange={(audit_date) => onFormChange({ audit_date })}
      />
      <AuditNativeSelectField
        id="a5s-audit-area"
        label="Área auditada"
        value={form.area_id}
        onChange={(area_id) => onFormChange({ area_id })}
        placeholderOption="Selecione..."
        options={areas.map((area) => ({ value: area.id, label: area.name }))}
      />
      <div className="a5s-inline a5s-form__full">
        <NativeTextControl
          type="text"
          placeholder="Cadastrar nova área"
          value={newAreaName}
          onChange={onNewAreaNameChange}
        />
        <button type="button" className="a5s-btn a5s-btn--ghost" onClick={() => void onCreateArea()}>
          Adicionar área
        </button>
      </div>
      <AuditResponsiblePicker
        value={{
          user_id: null,
          display_name: form.area_responsible,
        }}
        disabled={loading}
        label="Responsável pela área"
        hint="Busque e selecione o responsável pela área auditada no Minha Delpi."
        searchAriaLabel="Buscar responsável da área por nome ou e-mail"
        onChange={(responsible) => onFormChange({ area_responsible: responsible.display_name })}
      />
      <AuditNativeSelectField
        id="a5s-audit-shift"
        label="Turno"
        value={form.shift}
        onChange={(shift) => onFormChange({ shift })}
        options={SHIFTS.map((shift) => ({ value: shift.value, label: shift.label }))}
      />

      <AuditAuditorPicker
        value={selectedAuditors}
        onChange={onAuditorsChange}
        disabled={loading}
      />

      <button
        type="button"
        className="a5s-btn"
        disabled={!canSubmit || loading}
        onClick={() => void onSubmit()}
      >
        {loading ? "Salvando..." : submitLabel}
      </button>
    </section>
  );
}
