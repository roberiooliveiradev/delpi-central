import { useEffect, useMemo, useState } from "react";
import type {
  SettingsGoalItem,
  SettingsGovernanceItem,
  SettingsParameterItem,
  SettingsWeightItem,
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
} from "../../data/types/settings";
import {
  buildSettingsPayloadFromResponse,
  hasSettingsChanged,
} from "../../utils/settingsComparison";
import { SettingsGoalsForm } from "./SettingsGoalsForm";
import { SettingsGovernanceForm } from "./SettingsGovernanceForm";
import { SettingsParametersForm } from "./SettingsParametersForm";
import { SettingsWeightsForm } from "./SettingsWeightsForm";

type SettingsStructuredEditorProps = {
  data: StrategicIndicatorsSettingsResponse;
  saving: boolean;
  onSave: (payload: StrategicIndicatorsSettingsUpdateRequest) => Promise<void>;
};

export function SettingsStructuredEditor({
  data,
  saving,
  onSave,
}: SettingsStructuredEditorProps) {
  const [weights, setWeights] = useState<SettingsWeightItem[]>([]);
  const [goals, setGoals] = useState<SettingsGoalItem[]>([]);
  const [parameters, setParameters] = useState<SettingsParameterItem[]>([]);
  const [governance, setGovernance] = useState<SettingsGovernanceItem[]>([]);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    setWeights(data.weights.items);
    setGoals(data.goals.items);
    setParameters(data.parameters.items);
    setGovernance(data.governance.items);
    setLocalError(null);
  }, [data]);

  const totalWeight = useMemo(
    () => weights.reduce((sum, item) => sum + Number(item.weight_pct || 0), 0),
    [weights],
  );

  const currentPayload = useMemo<StrategicIndicatorsSettingsUpdateRequest>(
    () => ({
      weights: { items: weights },
      goals: { items: goals },
      parameters: { items: parameters },
      governance: { items: governance },
    }),
    [weights, goals, parameters, governance],
  );

  const originalPayload = useMemo(
    () => buildSettingsPayloadFromResponse(data),
    [data],
  );

  const dirty = useMemo(
    () => hasSettingsChanged(originalPayload, currentPayload),
    [originalPayload, currentPayload],
  );

  function handleReset() {
    setWeights(data.weights.items);
    setGoals(data.goals.items);
    setParameters(data.parameters.items);
    setGovernance(data.governance.items);
    setLocalError(null);
  }

  async function handleSave() {
    setLocalError(null);

    if (totalWeight !== 100) {
      setLocalError(`A soma dos pesos deve ser 100. Valor atual: ${totalWeight}.`);
      return;
    }

    if (!dirty) {
      setLocalError("Nenhuma alteração pendente para salvar.");
      return;
    }

    await onSave(currentPayload);
  }

  return (
    <section className="si-settings-editor">
      <div className="si-settings-editor__header">
        <div>
          <h3 className="si-settings-editor__title">Edição administrativa</h3>
          <span className="si-settings-editor__subtitle">
            integração real com a API do módulo
          </span>
        </div>

        <div className="si-settings-editor__meta-group">
          <div className="si-settings-editor__summary">
            <span>Peso total atual</span>
            <strong>{totalWeight}%</strong>
          </div>

          <div
            className={`si-settings-editor__status ${
              dirty ? "si-settings-editor__status--warning" : "si-settings-editor__status--ok"
            }`}
          >
            {dirty ? "Alterações pendentes" : "Sem alterações pendentes"}
          </div>
        </div>
      </div>

      {localError ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--error">
          {localError}
        </div>
      ) : null}

      <div className="si-settings-editor__sections">
        <EditorSection
          title="Pesos por departamento"
          description="Estrutura oficial de composição do IGD."
        >
          <SettingsWeightsForm items={weights} onChange={setWeights} />
        </EditorSection>

        <EditorSection
          title="Metas resumidas"
          description="Objetivos executivos por área."
        >
          <SettingsGoalsForm items={goals} onChange={setGoals} />
        </EditorSection>

        <EditorSection
          title="Parâmetros globais"
          description="Configurações estruturais do módulo."
        >
          <SettingsParametersForm
            items={parameters}
            onChange={setParameters}
          />
        </EditorSection>

        <EditorSection
          title="Governança"
          description="Observações e parâmetros administrativos."
        >
          <SettingsGovernanceForm
            items={governance}
            onChange={setGovernance}
          />
        </EditorSection>
      </div>

      <div className="si-settings-editor__actions">
        <button
          type="button"
          className="si-settings-editor__button si-settings-editor__button--secondary"
          onClick={handleReset}
          disabled={saving || !dirty}
        >
          Resetar alterações
        </button>

        <button
          type="button"
          className="si-settings-editor__button"
          onClick={() => void handleSave()}
          disabled={saving || !dirty}
        >
          {saving ? "Salvando..." : "Salvar configurações"}
        </button>
      </div>
    </section>
  );
}

type EditorSectionProps = {
  title: string;
  description: string;
  children: React.ReactNode;
};

function EditorSection({
  title,
  description,
  children,
}: EditorSectionProps) {
  return (
    <article className="si-settings-editor__section">
      <div className="si-settings-editor__section-header">
        <h4 className="si-settings-editor__section-title">{title}</h4>
        <p className="si-settings-editor__section-description">{description}</p>
      </div>
      {children}
    </article>
  );
}