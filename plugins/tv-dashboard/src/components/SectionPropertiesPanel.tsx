import type { PlaylistSection } from "../api/tvDashboardApi";

type Props = {
  section: PlaylistSection;
  open: boolean;
  onClose: () => void;
  onSave: (patch: Partial<PlaylistSection>) => void;
};

/** Painel mínimo de propriedades da seção (duração, transição, ativo, master enabled). */
export function SectionPropertiesPanel({ section, open, onClose, onSave }: Props) {
  if (!open) return null;

  return (
    <div className="td-deck-section-props" role="dialog" aria-label="Propriedades da seção">
      <div className="td-deck-section-props__panel">
        <header className="td-deck-section-props__head">
          <h3>Propriedades da seção</h3>
          <button type="button" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </header>
        <label className="td-deck-section-props__field">
          <span>Nome</span>
          <input
            defaultValue={section.name}
            onBlur={(event) => {
              const name = event.target.value.trim();
              if (name && name !== section.name) onSave({ name });
            }}
          />
        </label>
        <label className="td-deck-section-props__field">
          <span>Duração padrão (s)</span>
          <input
            type="number"
            min={5}
            max={600}
            defaultValue={section.defaultDurationSec ?? ""}
            placeholder="Herdar playlist"
            onBlur={(event) => {
              const raw = event.target.value.trim();
              onSave({
                defaultDurationSec: raw ? Number(raw) : null,
              });
            }}
          />
        </label>
        <label className="td-deck-section-props__field">
          <span>Transição</span>
          <select
            defaultValue={section.transitionStyle ?? ""}
            onChange={(event) => {
              const value = event.target.value;
              onSave({ transitionStyle: value ? value : null });
            }}
          >
            <option value="">Herdar playlist</option>
            <option value="fade">Fade</option>
            <option value="slide">Slide</option>
            <option value="none">Nenhuma</option>
          </select>
        </label>
        <label className="td-deck-section-props__check">
          <input
            type="checkbox"
            defaultChecked={section.isActive !== false}
            onChange={(event) => onSave({ isActive: event.target.checked })}
          />
          <span>Visível na TV</span>
        </label>
        <label className="td-deck-section-props__check">
          <input
            type="checkbox"
            defaultChecked={Boolean(section.masterConfig?.enabled)}
            onChange={(event) =>
              onSave({
                masterConfig: {
                  ...(section.masterConfig ?? {}),
                  enabled: event.target.checked,
                },
              })
            }
          />
          <span>Master da seção ativo (fundo/logo)</span>
        </label>
        {section.masterConfig?.enabled ? (
          <label className="td-deck-section-props__field">
            <span>Cor de fundo da seção</span>
            <input
              type="color"
              defaultValue={
                section.masterConfig?.background?.type === "color"
                  ? section.masterConfig.background.value || "#0f172a"
                  : "#0f172a"
              }
              onChange={(event) =>
                onSave({
                  masterConfig: {
                    ...(section.masterConfig ?? {}),
                    enabled: true,
                    background: { type: "color", value: event.target.value },
                  },
                })
              }
            />
          </label>
        ) : null}
        <footer className="td-deck-section-props__foot">
          <button type="button" onClick={onClose}>
            Fechar
          </button>
        </footer>
      </div>
    </div>
  );
}
