type FilialSwitcherProps = {
  filiais: Array<{ id: string; label: string }>;
  value: string;
  onChange: (filialId: string) => void;
  compact?: boolean;
};

export function FilialSwitcher({
  filiais,
  value,
  onChange,
  compact = false,
}: FilialSwitcherProps) {
  if (filiais.length <= 1) {
    return null;
  }

  return (
    <div className={`pp-filial-switcher${compact ? " pp-filial-switcher--compact" : ""}`}>
      <p className="pp-filial-switcher__label">Filial</p>
      <div className="pp-filial-switcher__options" role="tablist" aria-label="Filiais">
        {filiais.map((filial) => {
          const active = value === filial.id;
          return (
            <button
              key={filial.id}
              type="button"
              role="tab"
              aria-selected={active}
              className={`pp-filial-switcher__option${active ? " is-active" : ""}`}
              onClick={() => onChange(filial.id)}
              title={`Filial ${filial.id}`}
            >
              <span className="pp-filial-switcher__option-label">{filial.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
