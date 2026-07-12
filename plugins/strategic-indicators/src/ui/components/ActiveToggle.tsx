import "./ActiveToggle.css";
import { SiNativeSwitchControl } from "./siNativeFormFields";

type ActiveToggleProps = {
  active: boolean;
  disabled?: boolean;
  onToggle: (nextActive: boolean) => void;
  ariaLabel?: string;
};

export function ActiveToggle({
  active,
  disabled = false,
  onToggle,
  ariaLabel = "Alternar situação ativa",
}: ActiveToggleProps) {
  return (
    <SiNativeSwitchControl
      className={`si-active-toggle ${active ? "is-on" : ""} ${disabled ? "is-disabled" : ""}`}
      inputClassName="si-active-toggle__input"
      trackClassName="si-active-toggle__track"
      checked={active}
      disabled={disabled}
      aria-label={ariaLabel}
      onChange={onToggle}
      label={<span className="si-active-toggle__label">{active ? "Ativo" : "Inativo"}</span>}
    />
  );
}
