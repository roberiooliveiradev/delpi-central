import { useEffect, useState } from "react";
import type {
  StrategicIndicatorsSettingsResponse,
  StrategicIndicatorsSettingsUpdateRequest,
} from "../../data/types/settings";

type SettingsEditorPanelProps = {
  data: StrategicIndicatorsSettingsResponse;
  saving: boolean;
  onSave: (payload: StrategicIndicatorsSettingsUpdateRequest) => Promise<void>;
};

export function SettingsEditorPanel({
  data,
  saving,
  onSave,
}: SettingsEditorPanelProps) {
  const [weightsJson, setWeightsJson] = useState("");
  const [goalsJson, setGoalsJson] = useState("");
  const [parametersJson, setParametersJson] = useState("");
  const [governanceJson, setGovernanceJson] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    setWeightsJson(JSON.stringify(data.weights, null, 2));
    setGoalsJson(JSON.stringify(data.goals, null, 2));
    setParametersJson(JSON.stringify(data.parameters, null, 2));
    setGovernanceJson(JSON.stringify(data.governance, null, 2));
  }, [data]);

  async function handleSave() {
    setLocalError(null);

    try {
      const payload: StrategicIndicatorsSettingsUpdateRequest = {
        weights: JSON.parse(weightsJson),
        goals: JSON.parse(goalsJson),
        parameters: JSON.parse(parametersJson),
        governance: JSON.parse(governanceJson),
      };

      await onSave(payload);
    } catch (err) {
      setLocalError(
        err instanceof Error
          ? err.message
          : "Falha ao interpretar ou salvar o JSON.",
      );
    }
  }

  return (
    <section className="si-settings-editor">
      <div className="si-settings-editor__header">
        <h3 className="si-settings-editor__title">Edição administrativa</h3>
        <span className="si-settings-editor__subtitle">
          integração real inicial com a API do módulo
        </span>
      </div>

      {localError ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--error">
          {localError}
        </div>
      ) : null}

      <div className="si-settings-editor__grid">
        <EditorBlock
          title="weights"
          value={weightsJson}
          onChange={setWeightsJson}
        />
        <EditorBlock
          title="goals"
          value={goalsJson}
          onChange={setGoalsJson}
        />
        <EditorBlock
          title="parameters"
          value={parametersJson}
          onChange={setParametersJson}
        />
        <EditorBlock
          title="governance"
          value={governanceJson}
          onChange={setGovernanceJson}
        />
      </div>

      <div className="si-settings-editor__actions">
        <button
          type="button"
          className="si-settings-editor__button"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? "Salvando..." : "Salvar configurações"}
        </button>
      </div>
    </section>
  );
}

type EditorBlockProps = {
  title: string;
  value: string;
  onChange: (value: string) => void;
};

function EditorBlock({ title, value, onChange }: EditorBlockProps) {
  return (
    <article className="si-settings-editor__block">
      <label className="si-settings-editor__label">{title}</label>
      <textarea
        className="si-settings-editor__textarea"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        spellCheck={false}
      />
    </article>
  );
}