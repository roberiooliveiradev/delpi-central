import { useState } from "react";

import { ActionButton, FileDropzone } from "@delpi/plugin-ui/index";
import {
  BpmnModelerApiError,
  importModel,
  inspectImport,
  type InspectResult,
} from "../data/api/bpmnModelerApi";
import {
  BPMNM_FILE_DROPZONE_LABELS,
  BpmnmModal,
  BpmnmStateBanner,
  BpmnmTextField,
  bpmnmFileDropzoneClasses,
} from "@delpi/bpmn-editor";

type Props = {
  open: boolean;
  getAccessToken?: () => string | undefined;
  onCancel: () => void;
  onImported: (modelId: string) => void;
};

type Step = "pick" | "inspecting" | "result" | "creating";

/** Import multi-step (P4 §20): arquivo → intake → resultado → nome → criar. */
export function ImportDialog({ open, getAccessToken, onCancel, onImported }: Props) {
  const [step, setStep] = useState<Step>("pick");
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [result, setResult] = useState<InspectResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // reset na abertura — adjust-state-during-render (sem setState em effect)
  const [wasOpen, setWasOpen] = useState(open);
  if (wasOpen !== open) {
    setWasOpen(open);
    if (open) {
      setStep("pick");
      setFile(null);
      setResult(null);
      setError(null);
    }
  }

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
    <BpmnmModal
      open={open}
      title="Importar BPMN"
      onClose={onCancel}
      initialFocusSelector="input[type='file']"
      footer={
        <>
          <ActionButton
            type="button"
            onClick={onCancel}
            disabled={step === "creating"}
          >
            Cancelar
          </ActionButton>
          {step === "result" && eligible && (
            <ActionButton
              variant="primary"
              type="button"
              disabled={name.trim().length === 0}
              onClick={() => void confirm()}
            >
              Importar
            </ActionButton>
          )}
          {step === "creating" && <span className="bpmnm-hint">Importando…</span>}
        </>
      }
    >
      {step === "pick" && (
        <>
          {error ? (
            <BpmnmStateBanner variant="error" className="bpmnm-error">
              {error}
            </BpmnmStateBanner>
          ) : null}
          <FileDropzone
            accept=".bpmn,.xml,application/xml,text/xml"
            onFilesSelected={(files) => {
              const selected = files[0];
              if (selected) void inspect(selected);
            }}
            classNames={bpmnmFileDropzoneClasses}
            labels={BPMNM_FILE_DROPZONE_LABELS}
            ariaLabel="Selecionar arquivo BPMN"
          />
        </>
      )}

      {step === "inspecting" && <p className="bpmnm-hint">Inspecionando arquivo…</p>}

      {(step === "result" || step === "creating") && result && (
        <>
          <p>
            Estado reconhecido: <code>{result.recognition_state}</code>
            {issueCount > 0 ? ` — ${issueCount} diagnóstico(s)` : ""}
          </p>
          {!eligible && (
            <BpmnmStateBanner variant="error" className="bpmnm-error">
              Este arquivo não pode ser importado.
            </BpmnmStateBanner>
          )}
          {error ? (
            <BpmnmStateBanner variant="error" className="bpmnm-error">
              {error}
            </BpmnmStateBanner>
          ) : null}
          {eligible && (
            <BpmnmTextField
              label="Nome do modelo"
              value={name}
              onChange={setName}
              required
            />
          )}
        </>
      )}

    </BpmnmModal>
  );
}
