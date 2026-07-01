import { useRef } from "react";
import { Plus, Trash2 } from "lucide-react";

import { upsertFiveWhys } from "../api/actionPlansApi";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FormActions } from "./ui/FormActions";
import { SectionSaveButton } from "./ui/SectionSaveButton";
import { FieldLabel, TitleWithHelp } from "./ui/HelpTooltip";
import { SelectField } from "./ui/SelectField";
import { TextAreaField } from "./ui/TextAreaField";
import type { FiveWhysForm, FiveWhyStep } from "../utils/fiveWhys";
import { isFilledWhyStep, serializeFiveWhysForm } from "../utils/fiveWhys";

const CONFIDENCE_OPTIONS = [
  { value: "low", label: "Baixa" },
  { value: "medium", label: "Média" },
  { value: "high", label: "Alta" },
];

type TrackKey = "occurrence" | "detection";

type TrackConfig = {
  key: TrackKey;
  title: string;
  addLabel: string;
  hint: string;
};

const TRACKS: TrackConfig[] = [
  {
    key: "occurrence",
    title: "Análise sobre a causa do problema (Ocorrência)",
    addLabel: "Adicionar porquê (ocorrência)",
    hint: PAC_HELP_TOOLTIPS.detail.fiveWhysOccurrence,
  },
  {
    key: "detection",
    title: "Análise sobre o motivo pelo qual não foi detectado (Detecção)",
    addLabel: "Adicionar porquê (detecção)",
    hint: PAC_HELP_TOOLTIPS.detail.fiveWhysDetection,
  },
];

type Props = {
  planId: string;
  form: FiveWhysForm;
  saving: string | null;
  dirty?: boolean;
  onChange: (form: FiveWhysForm) => void;
  onSave: (key: string, action: () => Promise<void>) => Promise<void>;
  expectedRevisionNumber?: number | null;
};

function updateTrack(
  form: FiveWhysForm,
  track: TrackKey,
  updater: (steps: FiveWhyStep[]) => FiveWhyStep[],
): FiveWhysForm {
  return { ...form, [track]: updater(form[track]) };
}

function WhysFlowTrack({
  config,
  steps,
  disabled,
  onChange,
}: {
  config: TrackConfig;
  steps: FiveWhyStep[];
  disabled: boolean;
  onChange: (steps: FiveWhyStep[]) => void;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);

  function setStep(index: number, patch: Partial<FiveWhyStep>) {
    onChange(
      steps.map((item, currentIndex) =>
        currentIndex === index ? { ...item, ...patch } : item,
      ),
    );
  }

  function removeStep(index: number) {
    const next = steps.filter((_, currentIndex) => currentIndex !== index);
    onChange(next.length ? next : [{ question: "", answer: "" }]);
  }

  function addStep() {
    onChange([...steps, { question: "", answer: "" }]);
    requestAnimationFrame(() => {
      const container = scrollRef.current;
      if (!container) {
        return;
      }
      container.scrollTo({ left: container.scrollWidth, behavior: "smooth" });
    });
  }

  return (
    <div className="pac-whys-flow">
      <h3 className="pac-whys-flow__track-title">
        <TitleWithHelp title={config.title} hint={config.hint} />
      </h3>
      <div
        ref={scrollRef}
        className="pac-whys-flow__track-scroll"
        role="region"
        aria-label={`${config.title} — deslize horizontalmente para ver todos os passos`}
        tabIndex={0}
      >
        <div className="pac-whys-flow__track">
          {steps.map((step, index) => (
            <div key={`${config.key}-${index}`} className="pac-whys-flow__segment">
              {index > 0 ? (
                <div className="pac-whys-flow__connector" aria-hidden="true">
                  <span className="pac-whys-flow__therefore">Portanto</span>
                  <span className="pac-whys-flow__arrow pac-whys-flow__arrow--back">↩</span>
                  <span className="pac-whys-flow__pq">PQ</span>
                  <span className="pac-whys-flow__arrow pac-whys-flow__arrow--fwd">→</span>
                </div>
              ) : null}

              <div className="pac-whys-flow__step">
                <div className="pac-whys-flow__step-header">
                  <span className="pac-whys-flow__step-index">{index + 1}</span>
                  <button
                    type="button"
                    className="pac-ghost-btn pac-ghost-btn--icon pac-ghost-btn--danger"
                    title="Remover porquê"
                    disabled={disabled || (steps.length === 1 && !isFilledWhyStep(step))}
                    onClick={() => removeStep(index)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <label
                  className="pac-whys-flow__step-label"
                  htmlFor={`pac-whys-${config.key}-${index}-question`}
                >
                  <FieldLabel
                    label={`${index + 1}º porquê — pergunta`}
                    hint={PAC_HELP_TOOLTIPS.detail.fiveWhysQuestion}
                  />
                </label>
                <textarea
                  id={`pac-whys-${config.key}-${index}-question`}
                  className="pac-whys-flow__input pac-whys-flow__input--question"
                  value={step.question}
                  placeholder="Por que…?"
                  rows={2}
                  disabled={disabled}
                  onChange={(event) => setStep(index, { question: event.target.value })}
                />

                <label
                  className="pac-whys-flow__step-label"
                  htmlFor={`pac-whys-${config.key}-${index}-answer`}
                >
                  <FieldLabel
                    label="Resposta"
                    hint={PAC_HELP_TOOLTIPS.detail.fiveWhysAnswer}
                  />
                </label>
                <textarea
                  id={`pac-whys-${config.key}-${index}-answer`}
                  className="pac-whys-flow__input pac-whys-flow__input--answer"
                  value={step.answer}
                  placeholder="Porque…"
                  rows={3}
                  disabled={disabled}
                  onChange={(event) => setStep(index, { answer: event.target.value })}
                />
              </div>
            </div>
          ))}

          <button
            type="button"
            className="pac-whys-flow__add"
            disabled={disabled}
            onClick={addStep}
          >
            <Plus size={16} />
            <span>{config.addLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export function FiveWhysFlowPanel({
  planId,
  form,
  saving,
  dirty = false,
  onChange,
  onSave,
  expectedRevisionNumber,
}: Props) {
  const busy = saving === "five-whys";

  return (
    <>
      {TRACKS.map((track) => (
        <WhysFlowTrack
          key={track.key}
          config={track}
          steps={form[track.key]}
          disabled={busy}
          onChange={(steps) => onChange(updateTrack(form, track.key, () => steps))}
        />
      ))}

      <div className="pac-form-grid pac-whys-flow__footer">
        <TextAreaField
          id="pac-root-cause"
          label="Causa raiz"
          hint={PAC_HELP_TOOLTIPS.form.rootCause}
          value={form.root_cause}
          onChange={(root_cause) => onChange({ ...form, root_cause })}
          rows={4}
          fullWidth
        />
        <SelectField
          id="pac-five-whys-confidence"
          label="Confiança na causa raiz"
          hint={PAC_HELP_TOOLTIPS.form.confidence}
          options={CONFIDENCE_OPTIONS}
          value={form.confidence_level}
          onChange={(confidence_level) => onChange({ ...form, confidence_level })}
          searchable={false}
        />
      </div>

      <FormActions>
        <SectionSaveButton
          saveKey="five-whys"
          saving={saving}
          dirty={dirty}
          label="Salvar porquês"
          onSave={() =>
            void onSave("five-whys", async () => {
              await upsertFiveWhys(
                planId,
                serializeFiveWhysForm(form),
                expectedRevisionNumber,
              );
            })
          }
        />
      </FormActions>
    </>
  );
}
