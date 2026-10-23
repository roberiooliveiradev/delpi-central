import { useId } from "react";

import type { DictationMode } from "../audio/dictationMode";

export type DictationModeSettingsProps = {
  value: DictationMode;
  onChange: (mode: DictationMode) => void;
  disabled?: boolean;
  liveAvailable: boolean;
};

/**
 * Seção "Ditado" do menu Configurações do campo de pergunta.
 * Escolha exclusiva batch/live com descrições honestas; não conhece STT,
 * provider, backend nem sessões — o host controla valor e disponibilidade.
 */
export function DictationModeSettings({
  value,
  onChange,
  disabled = false,
  liveAvailable,
}: DictationModeSettingsProps) {
  const groupId = useId();
  const liveDisabled = disabled || !liveAvailable;
  const liveSelectedButUnavailable = value === "live" && !liveAvailable;
  return (
    <fieldset className="delia-dictation-settings" disabled={disabled}>
      <legend className="delia-dictation-settings__legend">Ditado</legend>
      <label className="delia-dictation-settings__option" data-checked={value === "batch"}>
        <input
          type="radio"
          name={groupId}
          checked={value === "batch"}
          disabled={disabled}
          onChange={() => onChange("batch")}
        />
        <span className="delia-dictation-settings__text">
          <span className="delia-dictation-settings__label">
            Gravar e transcrever
          </span>
          <span className="delia-dictation-settings__hint">
            Grave primeiro e receba o texto ao finalizar.
          </span>
        </span>
      </label>
      <label
        className="delia-dictation-settings__option"
        data-checked={value === "live"}
        data-disabled={liveDisabled}
      >
        <input
          type="radio"
          name={groupId}
          checked={value === "live"}
          disabled={liveDisabled}
          onChange={() => onChange("live")}
        />
        <span className="delia-dictation-settings__text">
          <span className="delia-dictation-settings__label">
            Transcrição em tempo real
          </span>
          <span className="delia-dictation-settings__hint">
            {liveSelectedButUnavailable
              ? "Indisponível no momento — usando Gravar e transcrever na próxima gravação."
              : !liveAvailable
                ? "Indisponível no momento."
                : "Veja o texto aparecer durante a fala."}
          </span>
        </span>
      </label>
    </fieldset>
  );
}
