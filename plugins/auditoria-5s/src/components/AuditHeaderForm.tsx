import type { AuditArea } from "../api/audit5sApi";
import { SHIFTS } from "../constants/audit5s";
import type { AuditAuditorSelection } from "../types/auditAuditor";
import { AuditAuditorPicker } from "./AuditAuditorPicker";

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
      <label>
        Data
        <input
          type="date"
          value={form.audit_date}
          onChange={(e) => onFormChange({ audit_date: e.target.value })}
        />
      </label>
      <label>
        Área auditada
        <select value={form.area_id} onChange={(e) => onFormChange({ area_id: e.target.value })}>
          <option value="">Selecione...</option>
          {areas.map((area) => (
            <option key={area.id} value={area.id}>
              {area.name}
            </option>
          ))}
        </select>
      </label>
      <div className="a5s-inline a5s-form__full">
        <input
          type="text"
          placeholder="Cadastrar nova área"
          value={newAreaName}
          onChange={(e) => onNewAreaNameChange(e.target.value)}
        />
        <button type="button" className="a5s-btn a5s-btn--ghost" onClick={() => void onCreateArea()}>
          Adicionar área
        </button>
      </div>
      <label>
        Responsável pela área
        <input
          type="text"
          value={form.area_responsible}
          onChange={(e) => onFormChange({ area_responsible: e.target.value })}
        />
      </label>
      <label>
        Turno
        <select value={form.shift} onChange={(e) => onFormChange({ shift: e.target.value })}>
          {SHIFTS.map((shift) => (
            <option key={shift.value} value={shift.value}>
              {shift.label}
            </option>
          ))}
        </select>
      </label>

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
