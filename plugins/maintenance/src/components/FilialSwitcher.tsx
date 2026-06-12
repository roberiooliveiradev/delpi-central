type FilialSwitcherProps = {
  filiais: Array<{ id: string; label: string }>;
  value: string;
  onChange: (filialId: string) => void;
};

export function FilialSwitcher({ filiais, value, onChange }: FilialSwitcherProps) {
  if (filiais.length <= 1) {
    return null;
  }

  return (
    <section className="dm-card dm-filial-switcher" aria-label="Seleção de filial">
      <div className="dm-filial-switcher__header">
        <p className="dm-filial-switcher__label">Filial operacional</p>
        <p className="dm-filial-switcher__hint">
          Escolha a filial para ver os submódulos disponíveis.
        </p>
      </div>
      <div className="dm-filial-switcher__options" role="tablist" aria-label="Filiais">
        {filiais.map((filial) => {
          const active = value === filial.id;
          return (
            <button
              key={filial.id}
              type="button"
              role="tab"
              aria-selected={active}
              className={`dm-filial-switcher__option${active ? " is-active" : ""}`}
              onClick={() => onChange(filial.id)}
              title={`Filial ${filial.id}`}
            >
              <span className="dm-filial-switcher__option-label">{filial.label}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
