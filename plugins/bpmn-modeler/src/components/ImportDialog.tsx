import { useRef, useState } from "react";

import {
  BpmnModelerApiError,
  importModel,
  inspectImport,
  type InspectResult,
} from "../data/api/bpmnModelerApi";

type Props = {
  open: boolean;
  getAccessToken?: () => string | undefined;
  onCancel: () => void;
  onImported: (modelId: string) => void;
};

type Step = "pick" | "inspecting" | "result" | "creating";

/** Import multi-step (P4 §20): arquivo → intake → resultado → nome → criar. */
export function ImportDialog({ open, getAccessToken, onCancel, onImported }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<Step>("pick");
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [result, setResult] = useState<InspectResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setStep("pick");
    setFile(null);
    setResult(null);
    setError(null);
    onCancel();
  };

  const inspect = async (selected: File) => {
    setFile(selected);
    setName(selected.name.replace(/\.(bpmn|xml)$/i, ""));
    setStep("inspecting");
    setError(null);
    try {
      const inspection = await inspectImport(selected, { getAccessToken });
      setResult(inspection);
      setStep("result");
    } catch (err) {
      setError(
        err instanceof BpmnModelerApiError
          ? err.message
          : "Falha ao inspecionar o arquivo.",
      );
      setStep("pick");
    }
  };

  const confirm = async () => {
    if (!file) return;
    setStep("creating");
    try {
      const outcome = await importModel(file, name.trim(), { getAccessToken });
      onImported(outcome.model_id);
    } catch (err) {
      if (err instanceof BpmnModelerApiError && err.code === "VALIDATION_BLOCKED") {
        setError(err.message);
        setStep("result");
      } else {
        setError(err instanceof Error ? err.message : "Falha ao importar.");
        setStep("result");
      }
    }
  };

  const issueCount = result?.validation_report.issues.length ?? 0;
  const eligible = result?.eligible_to_import === true;

  return (
    <div className="bpmnm-overlay" role="presentation">
      <div className="bpmnm-dialog" role="dialog" aria-modal="true" aria-labelledby="bpmnm-import-title">
        <h2 id="bpmnm-import-title">Importar BPMN</h2>

        {step === "pick" && (
          <>
            {error ? <p className="bpmnm-error">{error}</p> : null}
            <input
              ref={fileRef}
              type="file"
              accept=".bpmn,.xml,application/xml,text/xml"
              onChange={(e) => {
                const selected = e.target.files?.[0];
                if (selected) void inspect(selected);
              }}
            />
          </>
        )}

        {step === "inspecting" && <p>Inspecionando arquivo…</p>}

        {(step === "result" || step === "creating") && result && (
          <>
            <p>
              Estado reconhecido: <code>{result.recognition_state}</code>
              {issueCount > 0 ? ` — ${issueCount} diagnóstico(s)` : ""}
            </p>
            {!eligible && (
              <p className="bpmnm-error">
                Este arquivo não pode ser importado.
              </p>
            )}
            {error ? <p className="bpmnm-error">{error}</p> : null}
            {eligible && (
              <label className="bpmnm-field">
                Nome do modelo
                <input
                  type="text"
                  value={name}
                  maxLength={120}
                  onChange={(e) => setName(e.target.value)}
                />
              </label>
            )}
          </>
        )}

        <div className="bpmnm-dialog__actions">
          <button type="button" onClick={reset} className="bpmnm-btn" disabled={step === "creating"}>
            Cancelar
          </button>
          {step === "result" && eligible && (
            <button
              type="button"
              className="bpmnm-btn bpmnm-btn--primary"
              disabled={name.trim().length === 0}
              onClick={() => void confirm()}
            >
              Importar
            </button>
          )}
          {step === "creating" && <span>Importando…</span>}
        </div>
      </div>
    </div>
  );
}
