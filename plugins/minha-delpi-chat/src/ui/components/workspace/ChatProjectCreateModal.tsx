import { Plus, X } from "lucide-react";
import { useState } from "react";

import type { ChatProject, CreateChatProjectPayload } from "../../../data/api/chatTypes";

import { ChatModal } from "../shared/modal/ChatModal";
import "./ChatProjectCreateModal.css";

const PROJECT_ICON_OPTIONS = ["📁", "📊", "🏭", "🔬", "✅", "🎯", "📦", "💡", "🛠️", "📋"] as const;
const DEFAULT_PROJECT_ICON = PROJECT_ICON_OPTIONS[0];

type ChatProjectCreateModalProps = {
  open: boolean;
  onClose: () => void;
  onCreateProject?: (payload: CreateChatProjectPayload) => Promise<ChatProject | null>;
  onSelectProject?: (projectId: string | null) => void;
};

export function ChatProjectCreateModal({
  open,
  onClose,
  onCreateProject,
  onSelectProject,
}: ChatProjectCreateModalProps) {
  const [name, setName] = useState("");
  const [icon, setIcon] = useState<string>(DEFAULT_PROJECT_ICON);
  const [isSaving, setIsSaving] = useState(false);

  const canSubmit = name.trim().length >= 2 && !isSaving;

  function resetForm() {
    setName("");
    setIcon(DEFAULT_PROJECT_ICON);
  }

  async function handleSubmit() {
    if (!canSubmit) {
      return;
    }

    setIsSaving(true);

    try {
      const project = await onCreateProject?.({
        name: name.trim(),
        icon: icon.trim() || DEFAULT_PROJECT_ICON,
      });

      if (project) {
        onSelectProject?.(project.id);
      }

      resetForm();
      onClose();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <ChatModal
      open={open}
      onClose={onClose}
      size="none"
      panelClassName="mdc-chat-project-create-modal"
      ariaLabel="Criar projeto"
    >
      <header>
        <h2>Criar projeto</h2>

        <button type="button" onClick={onClose} aria-label="Fechar">
          <X size={18} aria-hidden="true" />
        </button>
      </header>

      <div className="mdc-chat-project-create-modal__field">
        <span>Ícone</span>
        <div
          className="mdc-chat-project-create-modal__icon-grid"
          role="listbox"
          aria-label="Ícone do projeto"
        >
          {PROJECT_ICON_OPTIONS.map((option) => {
            const isSelected = icon === option;

            return (
              <button
                key={option}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={
                  isSelected
                    ? "mdc-chat-project-create-modal__icon-option mdc-chat-project-create-modal__icon-option--active"
                    : "mdc-chat-project-create-modal__icon-option"
                }
                onClick={() => setIcon(option)}
                title={`Usar ícone ${option}`}
              >
                <span aria-hidden="true">{option}</span>
              </button>
            );
          })}
        </div>
      </div>

      <label className="mdc-chat-project-create-modal__field">
        <span>Nome do projeto</span>
        <span className="mdc-chat-project-create-modal__input-wrap">
          <span className="mdc-chat-project-create-modal__input-icon" aria-hidden="true">
            {icon}
          </span>
          <input
            value={name}
            autoFocus
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: Qualidade, Engenharia..."
            onKeyDown={(event) => {
              if (event.key === "Enter" && canSubmit) {
                event.preventDefault();
                void handleSubmit();
              }
            }}
          />
        </span>
      </label>

      <footer>
        <button type="button" className="mdc-chat-ws-toolbar-btn" onClick={onClose}>
          Cancelar
        </button>
        <button
          type="button"
          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
          onClick={() => void handleSubmit()}
          disabled={!canSubmit}
        >
          <Plus size={16} aria-hidden="true" />
          <span>{isSaving ? "Criando..." : "Criar projeto"}</span>
        </button>
      </footer>
    </ChatModal>
  );
}
