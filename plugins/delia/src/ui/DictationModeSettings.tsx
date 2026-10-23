import { useId } from "react";
import { Check, Mic } from "lucide-react";

import type { DictationMode } from "../audio/dictationMode";

export type DictationModeSettingsProps = {
  value: DictationMode;
  onChange: (mode: DictationMode) => void;
  disabled?: boolean;
  liveAvailable: boolean;
};

type OptionProps = {
  groupId: string;
  optionValue: DictationMode;
  selected: boolean;
  disabled: boolean;
  label: string;
  hint: string;
  onChange: (mode: DictationMode) => void;
};

/** Linha selecionável clean: radio nativo oculto + check discreto à direita. */
function DictationModeOption({
  groupId,
  optionValue,
  selected,
  disabled,
  label,
  hint,
  onChange,
}: OptionProps) {
  return (
    <label
      className="delia-dictation-settings__option"
      data-checked={selected}
      data-disabled={disabled}
    >
      <input
        type="radio"
        className="delia-dictation-settings__input"
        name={groupId}
        checked={selected}
        disabled={disabled}
        onChange={() => onChange(optionValue)}
      />
      <span className="delia-dictation-settings__text">
        <span className="delia-dictation-settings__label">{label}</span>
        <span className="delia-dictation-settings__hint">{hint}</span>
      </span>
      <Check
        className="delia-dictation-settings__check"
        size={15}
        strokeWidth={2}
        aria-hidden="true"
      />
    </label>
  );
}

/**
 * Seção "Ditado" do menu Configurações do campo de pergunta.
 * Linhas selecionáveis (clean select) sobre radios nativos — o host
 * controla valor e disponibilidade; zero conhecimento de STT/backend.
 */
export function DictationModeSettings({
  value,
  onChange,
  disabled = false,
  liveAvailable,
}: DictationModeSettingsProps) {
  const groupId = useId();
  const liveSelectedButUnavailable = value === "live" && !liveAvailable;
  return (
    <fieldset
      className="delia-dictation-settings"
      disabled={disabled}
    >
      <legend className="delia-dictation-settings__legend">
        <Mic size={12} strokeWidth={1.8} aria-hidden="true" />
        Ditado
      </legend>
      <DictationModeOption
        groupId={groupId}
        optionValue="batch"
        selected={value === "batch"}
        disabled={disabled}
        label="Gravar e transcrever"
        hint="Grave primeiro; o texto aparece ao finalizar."
        onChange={onChange}
      />
      <DictationModeOption
        groupId={groupId}
        optionValue="live"
        selected={value === "live"}
        disabled={disabled || !liveAvailable}
        label="Transcrição em tempo real"
        hint={
          liveSelectedButUnavailable
            ? "Indisponível no momento — usando Gravar e transcrever na próxima gravação."
            : !liveAvailable
              ? "Indisponível no momento."
              : "Veja o texto aparecer durante a fala."
        }
        onChange={onChange}
      />
    </fieldset>
  );
}
