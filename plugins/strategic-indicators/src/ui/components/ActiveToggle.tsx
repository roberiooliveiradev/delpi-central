import "./ActiveToggle.css";

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
    <label
      className={`si-active-toggle ${active ? "is-on" : ""} ${disabled ? "is-disabled" : ""}`}
      title={active ? "Ativo — clique para desativar" : "Inativo — clique para ativar"}
    >
      <input
        type="checkbox"
        className="si-active-toggle__input"
        checked={active}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(event) => onToggle(event.target.checked)}
      />
      <span className="si-active-toggle__track" aria-hidden="true">
        <span className="si-active-toggle__thumb" />
      </span>
      <span className="si-active-toggle__label">{active ? "Ativo" : "Inativo"}</span>
    </label>
  );
}
