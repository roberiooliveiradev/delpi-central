import { Check, Folder, Pencil, Plus, Share2, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { ChatAgent, ChatProject } from "../../data/api/chatTypes";
import { ChatConfirmDialog } from "./ChatConfirmDialog";

import "./ChatProjectsModal.css";

type ChatProjectsModalProps = {
  open: boolean;
  projects: ChatProject[];
  agents?: ChatAgent[];
  selectedProjectId?: string | null;
  isLoading?: boolean;
  onClose: () => void;
  onSelectProject?: (projectId: string | null) => void;
  onCreateProject?: (payload: {
    name: string;
    description?: string | null;
    instructions?: string | null;
    defaultAgentKey?: string | null;
    visibility?: string;
    icon?: string | null;
    color?: string | null;
  }) => Promise<ChatProject | null>;
  onUpdateProject?: (
    projectId: string,
    payload: {
      name?: string;
      description?: string | null;
      instructions?: string | null;
      defaultAgentKey?: string | null;
      visibility?: string;
      icon?: string | null;
      color?: string | null;
      archived?: boolean;
    },
  ) => Promise<ChatProject | null>;
  onRenameProject?: (projectId: string, name: string) => Promise<ChatProject | null>;
  onDeleteProject?: (projectId: string) => Promise<boolean>;
  onShareProject?: (
    projectId: string,
    payload: { targetUserId: string; role: string },
  ) => Promise<boolean>;
};

type ProjectFormMode = "create" | "edit";

function canEditProject(project: ChatProject): boolean {
  return ["owner", "editor"].includes(project.access_role);
}

function canDeleteProject(project: ChatProject): boolean {
  return project.access_role === "owner";
}

export function ChatProjectsModal({
  open,
  projects,
  agents = [],
  selectedProjectId,
  isLoading,
  onClose,
  onSelectProject,
  onCreateProject,
  onUpdateProject,
  onRenameProject,
  onDeleteProject,
  onShareProject,
}: ChatProjectsModalProps) {
  const [mode, setMode] = useState<ProjectFormMode>("create");
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ChatProject | null>(null);
  const [shareTarget, setShareTarget] = useState<ChatProject | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [defaultAgentKey, setDefaultAgentKey] = useState("");
  const [visibility, setVisibility] = useState("private");
  const [icon, setIcon] = useState("folder");
  const [color, setColor] = useState("blue");
  const [targetUserId, setTargetUserId] = useState("");
  const [shareRole, setShareRole] = useState("viewer");

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    startCreate();
    setDeleteTarget(null);
    setShareTarget(null);
  }, [open]);

  if (!open) {
    return null;
  }

  function startCreate() {
    setMode("create");
    setEditingProjectId(null);
    setName("");
    setDescription("");
    setInstructions("");
    setDefaultAgentKey("");
    setVisibility("private");
    setIcon("folder");
    setColor("blue");
    setTargetUserId("");
    setShareRole("viewer");
    setLocalError(null);
  }

  function startEdit(project: ChatProject) {
    setMode("edit");
    setEditingProjectId(project.id);
    setName(project.name);
    setDescription(project.description ?? "");
    setInstructions(project.instructions ?? "");
    setDefaultAgentKey(project.default_agent_key ?? "");
    setVisibility(project.visibility === "public" ? "public" : "private");
    setIcon(project.icon ?? "folder");
    setColor(project.color ?? "blue");
    setLocalError(null);
  }

  async function submitForm() {
    const normalizedName = name.trim();

    if (!normalizedName) {
      setLocalError("Informe o nome do projeto.");
      return;
    }

    const payload = {
      name: normalizedName,
      description: description.trim() || null,
      instructions: instructions.trim() || null,
      defaultAgentKey: defaultAgentKey || null,
      visibility,
      icon: icon.trim() || null,
      color: color.trim() || null,
    };

    if (mode === "create") {
      const created = await onCreateProject?.(payload);

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

    const updated = onUpdateProject
      ? await onUpdateProject(editingProjectId, payload)
      : await onRenameProject?.(editingProjectId, normalizedName);

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

  async function submitShare() {
    if (!shareTarget || !targetUserId.trim()) {
      setLocalError("Informe o ID do usuário que receberá acesso.");
      return;
    }

    const shared = await onShareProject?.(shareTarget.id, {
      targetUserId: targetUserId.trim(),
      role: shareRole,
    });

    if (shared) {
      setShareTarget(null);
      setTargetUserId("");
      setShareRole("viewer");
      setLocalError(null);
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
              Projetos separam conversas, documentos, agentes e instruções de trabalho.
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
                        <small>
                          {project.visibility} · {project.access_role}
                        </small>
                      </span>
                    </button>

                    <div className="mdc-chat-projects-modal__item-actions">
                      {canEditProject(project) ? (
                        <button
                          type="button"
                          onClick={() => startEdit(project)}
                          aria-label="Editar projeto"
                          title="Editar"
                        >
                          <Pencil size={15} aria-hidden="true" />
                        </button>
                      ) : null}

                      {project.access_role === "owner" ? (
                        <button
                          type="button"
                          onClick={() => setShareTarget(project)}
                          aria-label="Compartilhar projeto"
                          title="Compartilhar"
                        >
                          <Share2 size={15} aria-hidden="true" />
                        </button>
                      ) : null}

                      {canDeleteProject(project) ? (
                        <button
                          type="button"
                          onClick={() => setDeleteTarget(project)}
                          aria-label="Excluir projeto"
                          title="Excluir"
                        >
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      ) : null}
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
                  Crie um ambiente isolado para conversas, documentos e agentes.
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

            <div className="mdc-chat-projects-modal__grid">
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
                <span>Visibilidade</span>
                <select
                  value={visibility}
                  onChange={(event) => setVisibility(event.target.value)}
                >
                  <option value="private">Privado</option>
                  <option value="public">Público interno</option>
                </select>
              </label>
            </div>

            <label>
              <span>Descrição</span>
              <textarea
                value={description}
                maxLength={500}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Explique o objetivo deste projeto..."
              />
            </label>

            <label>
              <span>Instruções do projeto</span>
              <textarea
                value={instructions}
                className="mdc-chat-projects-modal__prompt"
                maxLength={12000}
                onChange={(event) => setInstructions(event.target.value)}
                placeholder="Instruções usadas nas conversas deste projeto..."
              />
            </label>

            <div className="mdc-chat-projects-modal__grid">
              <label>
                <span>Agente padrão</span>
                <select
                  value={defaultAgentKey}
                  onChange={(event) => setDefaultAgentKey(event.target.value)}
                >
                  <option value="">Sem agente padrão</option>
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.key}>
                      {agent.name}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>Ícone</span>
                <input
                  value={icon}
                  maxLength={60}
                  onChange={(event) => setIcon(event.target.value)}
                />
              </label>

              <label>
                <span>Cor</span>
                <input
                  value={color}
                  maxLength={40}
                  onChange={(event) => setColor(event.target.value)}
                />
              </label>
            </div>

            {shareTarget ? (
              <div className="mdc-chat-projects-modal__share">
                <strong>Compartilhar: {shareTarget.name}</strong>
                <div className="mdc-chat-projects-modal__grid">
                  <label>
                    <span>ID do usuário</span>
                    <input
                      value={targetUserId}
                      onChange={(event) => setTargetUserId(event.target.value)}
                    />
                  </label>

                  <label>
                    <span>Permissão</span>
                    <select
                      value={shareRole}
                      onChange={(event) => setShareRole(event.target.value)}
                    >
                      <option value="viewer">Visualizador</option>
                      <option value="editor">Editor</option>
                    </select>
                  </label>
                </div>

                <div className="mdc-chat-projects-modal__form-actions">
                  <button type="button" onClick={() => setShareTarget(null)}>
                    Cancelar
                  </button>
                  <button
                    type="button"
                    className="mdc-chat-projects-modal__primary"
                    onClick={() => void submitShare()}
                  >
                    Compartilhar
                  </button>
                </div>
              </div>
            ) : null}

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
