import { useMemo, useState } from "react";
import type { StrategicIndicatorsSettingsResponse } from "../../data/types/settings";
import { useSettingsDraft } from "../../state/hooks/useSettingsDraft";
import { SettingsWeightsForm } from "./SettingsWeightsForm";
import { SettingsGoalsForm } from "./SettingsGoalsForm";
import { SettingsParametersForm } from "./SettingsParametersForm";
import { SettingsGovernanceForm } from "./SettingsGovernanceForm";
import { Modal } from "./Modal";

type SettingsStructuredEditorProps = {
  data: StrategicIndicatorsSettingsResponse;
  saving?: boolean;
  onSave: (
    payload: Pick<
      StrategicIndicatorsSettingsResponse,
      "weights" | "goals" | "parameters" | "governance"
    >,
  ) => Promise<void>;
};

type EditorSection = "weights" | "goals" | "parameters" | "governance" | null;

export function SettingsStructuredEditor({
  data,
  saving = false,
  onSave,
}: SettingsStructuredEditorProps) {
  const {
    draft,
    errors,
    totalWeight,
    isDirty,
    isSaveDisabled,
    setWeightItems,
    setGoalItems,
    setParameterItems,
    setGovernanceItems,
    reset,
    validateAll,
  } = useSettingsDraft(data);

  const [openSection, setOpenSection] = useState<EditorSection>(null);
  const [sectionMessage, setSectionMessage] = useState<string | null>(null);

  const summary = useMemo(
    () => ({
      weightsCount: draft.weights.items.length,
      goalsCount: draft.goals.items.length,
      parametersCount: draft.parameters.items.length,
      governanceCount: draft.governance.items.length,
    }),
    [draft],
  );

  async function handleSaveAll() {
    const isValid = validateAll();
    if (!isValid) return;

    await onSave({
      weights: draft.weights,
      goals: draft.goals,
      parameters: draft.parameters,
      governance: draft.governance,
    });

    setSectionMessage("Configurações salvas com sucesso.");
    setOpenSection(null);
  }

  function handleCloseModal() {
    setOpenSection(null);
  }

  return (
    <section className="si-settings-admin-shell">
      <div className="si-settings-editor__header">
        <div className="si-settings-editor__meta-group">
          <div className="si-settings-editor__summary">
            <span>Blocos</span>
            <strong>4</strong>
          </div>

          <div className="si-settings-editor__summary">
            <span>Total dos pesos</span>
            <strong>{totalWeight}%</strong>
          </div>
        </div>
      </div>

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

      <div className="si-settings-admin-grid">
        <AdminCard
          title="Pesos"
          description="Distribuição oficial dos departamentos no cálculo do IGD."
          meta={`${summary.weightsCount} departamentos`}
          status={totalWeight === 100 ? "Total validado" : "Revisar total"}
          onEdit={() => setOpenSection("weights")}
        />

        <AdminCard
          title="Metas resumidas"
          description="Direcionadores executivos por departamento."
          meta={`${summary.goalsCount} registros`}
          status="Resumo executivo"
          onEdit={() => setOpenSection("goals")}
        />

        <AdminCard
          title="Parâmetros"
          description="Parâmetros globais do módulo e convenções oficiais."
          meta={`${summary.parametersCount} parâmetros`}
          status="Configuração global"
          onEdit={() => setOpenSection("parameters")}
        />

        <AdminCard
          title="Governança"
          description="Regras administrativas e observações estruturais do módulo."
          meta={`${summary.governanceCount} itens`}
          status="Políticas do módulo"
          onEdit={() => setOpenSection("governance")}
        />
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

      <Modal
        open={openSection === "weights"}
        onClose={handleCloseModal}
        title="Editar pesos"
        description="Ajuste a distribuição dos departamentos. O total deve permanecer em 100%."
        size="lg"
      >
        <SettingsWeightsForm
          items={draft.weights.items}
          onChange={setWeightItems}
        />
      </Modal>

      <Modal
        open={openSection === "goals"}
        onClose={handleCloseModal}
        title="Editar metas resumidas"
        description="Atualize os direcionadores executivos de cada departamento."
        size="lg"
      >
        <SettingsGoalsForm
          items={draft.goals.items}
          onChange={setGoalItems}
        />
      </Modal>

      <Modal
        open={openSection === "parameters"}
        onClose={handleCloseModal}
        title="Editar parâmetros"
        description="Atualize os parâmetros globais utilizados pela área administrativa."
        size="lg"
      >
        <SettingsParametersForm
          items={draft.parameters.items}
          onChange={setParameterItems}
        />
      </Modal>

      <Modal
        open={openSection === "governance"}
        onClose={handleCloseModal}
        title="Editar governança"
        description="Atualize notas e regras administrativas do módulo."
        size="lg"
      >
        <SettingsGovernanceForm
          items={draft.governance.items}
          onChange={setGovernanceItems}
        />
      </Modal>
    </section>
  );
}

function AdminCard({
  title,
  description,
  meta,
  status,
  onEdit,
}: {
  title: string;
  description: string;
  meta: string;
  status: string;
  onEdit: () => void;
}) {
  return (
    <article className="si-settings-admin-card">
      <div className="si-settings-admin-card__content">
        <div className="si-settings-admin-card__top">
          <h4 className="si-settings-admin-card__title">{title}</h4>
          <span className="si-settings-admin-card__status">{status}</span>
        </div>

        <p className="si-settings-admin-card__description">{description}</p>

        <div className="si-settings-admin-card__meta">{meta}</div>
      </div>

      <div className="si-settings-admin-card__actions">
        <button
          type="button"
          className="si-settings-editor__button si-settings-editor__button--secondary"
          onClick={onEdit}
        >
          Editar
        </button>
      </div>
    </article>
  );
}