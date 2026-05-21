import { useMemo, useState, type ReactNode } from "react";
import type {
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
} from "../../data/types/settings";
import { useSettingsDraft } from "../../state/hooks/useSettingsDraft";
import { SettingsParametersForm } from "./SettingsParametersForm";
import { SettingsGovernanceForm } from "./SettingsGovernanceForm";
import "./SettingsStructuredEditor.css";

type SettingsStructuredEditorProps = {
  data: StrategicIndicatorsSettingsResponse;
  saving?: boolean;
  onSave: (payload: StrategicIndicatorsSettingsUpdateRequest) => Promise<void>;
};

type EditorSection = "parameters" | "governance" | null;

export function SettingsStructuredEditor({
  data,
  saving = false,
  onSave,
}: SettingsStructuredEditorProps) {
  const {
    draft,
    errors,
    isDirty,
    isSaveDisabled,
    setParameterItems,
    setGovernanceItems,
    reset,
    validateAll,
  } = useSettingsDraft(data);

  const [openSection, setOpenSection] = useState<EditorSection>(null);
  const [sectionMessage, setSectionMessage] = useState<string | null>(null);

  const summary = useMemo(
    () => ({
      parametersCount: draft.parameters.items.length,
      governanceCount: draft.governance.items.length,
    }),
    [draft],
  );

  async function handleSaveAll() {
    const isValid = validateAll();
    if (!isValid) return;

    await onSave({
      parameters: draft.parameters,
      governance: draft.governance,
    });

    setSectionMessage("Configurações salvas com sucesso.");
    setOpenSection(null);
  }

  return (
    <section className="si-settings-admin-shell">
      {sectionMessage ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--success">
          {sectionMessage}
        </div>
      ) : null}

      {errors.root ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--error">
          {errors.root}
        </div>
      ) : null}

      <div className="si-settings-global-editor">
        <AdminExpandCard
          title="Parâmetros globais"
          description="Convenções e parâmetros centrais do módulo."
          meta={`${summary.parametersCount} parâmetros`}
          expanded={openSection === "parameters"}
          onToggle={() =>
            setOpenSection((current) =>
              current === "parameters" ? null : "parameters",
            )
          }
        >
          <SettingsParametersForm
            items={draft.parameters.items}
            onChange={setParameterItems}
          />
        </AdminExpandCard>

        <AdminExpandCard
          title="Governança"
          description="Regras administrativas e observações estruturais."
          meta={`${summary.governanceCount} itens`}
          expanded={openSection === "governance"}
          onToggle={() =>
            setOpenSection((current) =>
              current === "governance" ? null : "governance",
            )
          }
        >
          <SettingsGovernanceForm
            items={draft.governance.items}
            onChange={setGovernanceItems}
          />
        </AdminExpandCard>
      </div>

      <div className="si-settings-admin-actions">
        <button
          type="button"
          className="si-settings-editor__button si-settings-editor__button--secondary"
          onClick={() => {
            reset();
            setSectionMessage("Alterações descartadas.");
          }}
          disabled={saving || !isDirty}
        >
          Descartar alterações
        </button>

        <button
          type="button"
          className="si-settings-editor__button"
          onClick={() => void handleSaveAll()}
          disabled={saving || isSaveDisabled}
        >
          {saving ? "Salvando..." : "Salvar configurações"}
        </button>
      </div>
    </section>
  );
}

function AdminExpandCard({
  title,
  description,
  meta,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  description: string;
  meta: string;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <article className={`si-settings-expand-card ${expanded ? "is-expanded" : ""}`}>
      <button
        type="button"
        className="si-settings-expand-card__trigger"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <div className="si-settings-expand-card__text">
          <strong>{title}</strong>
          <span>{description}</span>
          <small>{meta}</small>
        </div>
        <span className="si-settings-expand-card__chevron">{expanded ? "−" : "+"}</span>
      </button>

      {expanded ? <div className="si-settings-expand-card__body">{children}</div> : null}
    </article>
  );
}
