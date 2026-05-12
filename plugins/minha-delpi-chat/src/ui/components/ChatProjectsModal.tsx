import { Check, Folder, Pencil, Plus, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatProject } from "../../data/api/chatTypes";
import { ChatConfirmDialog } from "./ChatConfirmDialog";

import "./ChatProjectsModal.css";

type ChatProjectsModalProps = {
  open: boolean;
  projects: ChatProject[];
  selectedProjectId?: string | null;
  isLoading?: boolean;
  onClose: () => void;
  onSelectProject?: (projectId: string | null) => void;
  onCreateProject?: (payload: {
    name: string;
    description?: string | null;
  }) => Promise<ChatProject | null>;
  onRenameProject?: (projectId: string, name: string) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
};

type ProjectFormMode = "create" | "edit";

export function ChatProjectsModal({
  open,
  projects,
  selectedProjectId,
  isLoading,
  onClose,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
}: ChatProjectsModalProps) {
  const [mode, setMode] = useState<ProjectFormMode>("create");
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<ChatProject | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    setMode("create");
    setEditingProjectId(null);
    setName("");
    setDescription("");
    setLocalError(null);
    setDeleteTarget(null);
  }, [open]);

  if (!open) {
    return null;
  }

  function startCreate() {
    setMode("create");
    setEditingProjectId(null);
    setName("");
    setDescription("");
    setLocalError(null);
  }

  function startEdit(project: ChatProject) {
    setMode("edit");
    setEditingProjectId(project.id);
    setName(project.name);
    setDescription(project.description ?? "");
    setLocalError(null);
  }

  async function submitForm() {
    const normalizedName = name.trim();
    const normalizedDescription = description.trim();

    if (!normalizedName) {
      setLocalError("Informe o nome do projeto.");
      return;
    }

    if (mode === "create") {
      const created = await onCreateProject?.({
        name: normalizedName,
        description: normalizedDescription || null,
      });

      if (created) {
        onSelectProject?.(created.id);
        startCreate();
      }

      return;
    }

    if (!editingProjectId) {
      setLocalError("Projeto inválido para edição.");
      return;
    }

    const updated = await onRenameProject?.(editingProjectId, normalizedName);

    if (updated) {
      startCreate();
    }
  }

  async function confirmDeleteProject() {
    if (!deleteTarget) {
      return;
    }

    const deleted = await onDeleteProject?.(deleteTarget.id);

    if (deleted) {
      if (selectedProjectId === deleteTarget.id) {
        onSelectProject?.(null);
      }

      setDeleteTarget(null);
      startCreate();
    }
  }

  return (
    <div
      className="mdc-chat-projects-modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <section
        className="mdc-chat-projects-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mdc-chat-projects-modal-title"
      >
        <header className="mdc-chat-projects-modal__header">
          <div>
            <p className="mdc-chat-eyebrow">Workspace</p>
            <h2 id="mdc-chat-projects-modal-title">Projetos</h2>
            <span>
              Projetos separam conversas, documentos e contexto de trabalho.
            </span>
          </div>

          <button type="button" onClick={onClose} aria-label="Fechar">
            <X size={18} aria-hidden="true" />
          </button>
        </header>

        <div className="mdc-chat-projects-modal__body">
          <aside className="mdc-chat-projects-modal__list">
            <button
              type="button"
              className={
                selectedProjectId
                  ? "mdc-chat-projects-modal__all"
                  : "mdc-chat-projects-modal__all mdc-chat-projects-modal__all--active"
              }
              onClick={() => onSelectProject?.(null)}
            >
              <Folder size={17} aria-hidden="true" />
              <span>Todos os projetos</span>
            </button>

            {isLoading ? (
              <p className="mdc-chat-muted">Carregando projetos...</p>
            ) : projects.length === 0 ? (
              <p className="mdc-chat-muted">Nenhum projeto criado ainda.</p>
            ) : (
              <div className="mdc-chat-projects-modal__items">
                {projects.map((project) => (
                  <article
                    key={project.id}
                    className={
                      project.id === selectedProjectId
                        ? "mdc-chat-projects-modal__item mdc-chat-projects-modal__item--active"
                        : "mdc-chat-projects-modal__item"
                    }
                  >
                    <button
                      type="button"
                      className="mdc-chat-projects-modal__item-main"
                      onClick={() => onSelectProject?.(project.id)}
                    >
                      <Folder size={17} aria-hidden="true" />
                      <span>
                        <strong>{project.name}</strong>
                        <small>{project.description || "Sem descrição"}</small>
                      </span>
                    </button>

                    <div className="mdc-chat-projects-modal__item-actions">
                      <button
                        type="button"
                        onClick={() => startEdit(project)}
                        aria-label="Editar projeto"
                        title="Editar"
                      >
                        <Pencil size={15} aria-hidden="true" />
                      </button>

                      <button
                        type="button"
                        onClick={() => setDeleteTarget(project)}
                        aria-label="Excluir projeto"
                        title="Excluir"
                      >
                        <Trash2 size={15} aria-hidden="true" />
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </aside>

          <form
            className="mdc-chat-projects-modal__form"
            onSubmit={(event) => {
              event.preventDefault();
              void submitForm();
            }}
          >
            <div className="mdc-chat-projects-modal__form-title">
              {mode === "create" ? (
                <Plus size={18} aria-hidden="true" />
              ) : (
                <Pencil size={18} aria-hidden="true" />
              )}
              <div>
                <h3>{mode === "create" ? "Novo projeto" : "Editar projeto"}</h3>
                <p>
                  {mode === "create"
                    ? "Crie um ambiente para conversas, documentos e agentes."
                    : "Atualize as informações do projeto selecionado."}
                </p>
              </div>
            </div>

            {selectedProject ? (
              <div className="mdc-chat-projects-modal__selected">
                Projeto ativo: <strong>{selectedProject.name}</strong>
              </div>
            ) : (
              <div className="mdc-chat-projects-modal__selected">
                Nenhum projeto ativo. Novas conversas ficarão em “Todos”.
              </div>
            )}

            <label>
              <span>Nome</span>
              <input
                value={name}
                maxLength={120}
                onChange={(event) => setName(event.target.value)}
                placeholder="Ex.: Qualidade, Engenharia, Produtos..."
              />
            </label>

            <label>
              <span>Descrição</span>
              <textarea
                value={description}
                maxLength={500}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique o objetivo deste projeto..."
              />
            </label>

            {localError ? (
              <p className="mdc-chat-projects-modal__error">{localError}</p>
            ) : null}

            <div className="mdc-chat-projects-modal__form-actions">
              {mode === "edit" ? (
                <button type="button" onClick={startCreate}>
                  Cancelar edição
                </button>
              ) : null}

              <button type="submit" className="mdc-chat-projects-modal__primary">
                <Check size={16} aria-hidden="true" />
                <span>{mode === "create" ? "Criar projeto" : "Salvar projeto"}</span>
              </button>
            </div>
          </form>
        </div>
      </section>

      <ChatConfirmDialog
        open={Boolean(deleteTarget)}
        danger
        title="Excluir projeto?"
        description={`O projeto "${
          deleteTarget?.name || "sem nome"
        }" será excluído. As conversas vinculadas deixam de pertencer a ele.`}
        confirmLabel="Excluir"
        cancelLabel="Cancelar"
        onConfirm={confirmDeleteProject}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
