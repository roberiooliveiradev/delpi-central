import { Save } from "lucide-react";

type SectionSaveButtonProps = {
  saveKey: string;
  saving: string | null;
  onSave: () => void;
  label?: string;
  dirty?: boolean;
  align?: "start" | "end";
  /** Sem largura total — uso em barra com botão «Adicionar» na mesma linha. */
  inline?: boolean;
};

export function SectionSaveButton({
  saveKey,
  saving,
  onSave,
  label = "Salvar",
  dirty = false,
  align = "end",
  inline = false,
}: SectionSaveButtonProps) {
  const busy = saving === saveKey;

  return (
    <div
      className={[
        "pac-section-save",
        `pac-section-save--${align}`,
        inline ? "pac-section-save--inline" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {dirty ? (
        <span className="pac-section-save__dirty" title="Há alterações não salvas neste bloco">
          Alterações não salvas
        </span>
      ) : null}
      <button
        type="button"
        className="pac-primary-btn"
        disabled={Boolean(saving) || !dirty}
        onClick={onSave}
      >
        <Save size={16} />
        {busy ? "Salvando…" : label}
      </button>
    </div>
  );
}
