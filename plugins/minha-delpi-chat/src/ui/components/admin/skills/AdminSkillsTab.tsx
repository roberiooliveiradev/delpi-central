import { Plus, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createAdminChatSkill,
  deactivateAdminChatSkill,
  listAdminChatSkills,
  updateAdminChatSkill,
} from "../../../../data/api/adminApi";
import type { AdminChatSkill, AdminRbacSummary } from "../../../../data/api/adminTypes";
import { AdminFormCheckbox } from "../shared/AdminFormCheckbox";
import { useConfirmDialog } from "../../useConfirmDialog";
import { SkillsSummaryStrip } from "./SkillsSummaryStrip";
import {
  computeSkillsSummary,
  filterSkillsByStatus,
  type SkillStatusFilter,
} from "./skillsSummary";

import "./AdminSkillsTab.css";

type AdminSkillsTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  rbac?: AdminRbacSummary | null;
};

type SkillDraft = {
  skillKey: string;
  label: string;
  description: string;
  policyContent: string;
  policyFile: string;
  metadataFlag: string;
  legacyMetadataFlag: string;
  executionPathHint: string;
  executionDerivedKey: string;
  isActive: boolean;
  sortOrder: number;
};

const EMPTY_DRAFT: SkillDraft = {
  skillKey: "",
  label: "",
  description: "",
  policyContent: "",
  policyFile: "",
  metadataFlag: "enabled",
  legacyMetadataFlag: "",
  executionPathHint: "",
  executionDerivedKey: "",
  isActive: true,
  sortOrder: 0,
};

function draftFromSkill(skill: AdminChatSkill): SkillDraft {
  return {
    skillKey: skill.skillKey,
    label: skill.label,
    description: skill.description,
    policyContent: skill.policyContent ?? "",
    policyFile: skill.policyFile ?? "",
    metadataFlag: skill.metadataFlag ?? "enabled",
    legacyMetadataFlag: skill.legacyMetadataFlag ?? "",
    executionPathHint: skill.executionPathHint ?? "",
    executionDerivedKey: skill.executionDerivedKey ?? "",
    isActive: skill.isActive,
    sortOrder: skill.sortOrder ?? 0,
  };
}

export function AdminSkillsTab({ getAccessToken, rbac }: AdminSkillsTabProps) {
  const canManage = Boolean(rbac?.capabilities.canManageTools);
  const { confirm, dialog: confirmDialog } = useConfirmDialog();

  const [skills, setSkills] = useState<AdminChatSkill[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<SkillDraft>(EMPTY_DRAFT);
  const [isCreating, setIsCreating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<SkillStatusFilter>("all");

  const summary = useMemo(() => computeSkillsSummary(skills), [skills]);
  const visibleSkills = useMemo(
    () => filterSkillsByStatus(skills, statusFilter),
    [skills, statusFilter],
  );

  const selectedSkill = useMemo(
    () => skills.find((item) => item.id === selectedId) ?? null,
    [skills, selectedId],
  );

  const loadSkills = useCallback(async () => {
    if (!getAccessToken) {
      setSkills([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const items = await listAdminChatSkills({ includeInactive: true }, { getAccessToken });
      setSkills(items);

      if (selectedId && !items.some((item) => item.id === selectedId)) {
        setSelectedId(null);
        setDraft(EMPTY_DRAFT);
        setIsCreating(false);
      }
    } catch {
      setError("Não foi possível carregar o catálogo de skills.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void loadSkills();
  }, [loadSkills]);

  function startCreate() {
    setIsCreating(true);
    setSelectedId(null);
    setDraft(EMPTY_DRAFT);
    setSuccess(null);
    setError(null);
  }

  function selectSkill(skill: AdminChatSkill) {
    setIsCreating(false);
    setSelectedId(skill.id);
    setDraft(draftFromSkill(skill));
    setSuccess(null);
    setError(null);
  }

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();

    if (!getAccessToken || !canManage) {
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccess(null);

    const payload = {
      skillKey: draft.skillKey.trim(),
      label: draft.label.trim(),
      description: draft.description.trim(),
      policyContent: draft.policyContent.trim() || null,
      policyFile: draft.policyFile.trim() || null,
      metadataFlag: draft.metadataFlag.trim() || "enabled",
      legacyMetadataFlag: draft.legacyMetadataFlag.trim() || null,
      executionPathHint: draft.executionPathHint.trim() || null,
      executionDerivedKey: draft.executionDerivedKey.trim() || null,
      isActive: draft.isActive,
      sortOrder: Number(draft.sortOrder) || 0,
    };

    try {
      if (isCreating) {
        const created = await createAdminChatSkill(payload, { getAccessToken });
        setSuccess("Skill criada com sucesso.");
        setIsCreating(false);
        setSelectedId(created.id);
        setDraft(draftFromSkill(created));
      } else if (selectedId) {
        const updated = await updateAdminChatSkill(selectedId, payload, { getAccessToken });
        setSuccess("Skill atualizada.");
        if (updated) {
          setDraft(draftFromSkill(updated));
        }
      }

      await loadSkills();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível salvar a skill.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeactivate() {
    if (!getAccessToken || !canManage || !selectedId) {
      return;
    }

    const confirmed = await confirm({
      title: "Desativar skill",
      description: "Desativar esta skill? Agentes deixarão de vê-la no catálogo.",
      confirmLabel: "Desativar",
      cancelLabel: "Cancelar",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await deactivateAdminChatSkill(selectedId, { getAccessToken });
      setSuccess("Skill desativada.");
      setSelectedId(null);
      setDraft(EMPTY_DRAFT);
      setIsCreating(false);
      await loadSkills();
    } catch {
      setError("Não foi possível desativar a skill.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="mdc-admin-skills" aria-label="Catálogo de habilidades">
      {confirmDialog}
      <header className="mdc-admin-page-header">
        <h2>Comportamentos</h2>
        <p>
          Cadastre comportamentos de prompt reutilizáveis. Cada agente escolhe quais habilidades
          estão ativas; a execução de APIs continua nas <strong>Actions</strong>.
        </p>
      </header>

      <div className="mdc-admin-skills__toolbar">
        <SkillsSummaryStrip
          summary={summary}
          activeFilter={statusFilter}
          isLoading={isLoading}
          onFilterChange={setStatusFilter}
        />

        <div className="mdc-admin-skills__toolbar-actions">
          <button
            type="button"
            className="mdc-admin-btn"
            onClick={() => void loadSkills()}
            disabled={isLoading}
            aria-label="Atualizar catálogo"
          >
            <RefreshCw size={15} aria-hidden="true" className={isLoading ? "is-spinning" : ""} />
            <span>Atualizar</span>
          </button>
          {canManage ? (
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
              onClick={startCreate}
            >
              <Plus size={15} aria-hidden="true" />
              <span>Nova habilidade</span>
            </button>
          ) : null}
        </div>
      </div>

      <div className="mdc-admin-skills__layout mdc-admin-split">
        <aside className="mdc-admin-split__aside mdc-admin-panel mdc-admin-skills__list-panel">
          <div className="mdc-admin-skills__list-toolbar">
            <strong>
              Catálogo
              {statusFilter !== "all"
                ? ` (${visibleSkills.length} de ${skills.length})`
                : ` (${skills.length})`}
            </strong>
          </div>

          {isLoading ? (
            <p className="mdc-admin-skills__muted">Carregando…</p>
          ) : visibleSkills.length === 0 ? (
            <p className="mdc-admin-skills__muted">
              {skills.length === 0
                ? "Nenhuma habilidade cadastrada."
                : "Nenhuma habilidade neste filtro."}
            </p>
          ) : (
            <ul className="mdc-admin-skills__list">
              {visibleSkills.map((skill) => (
                <li key={skill.id}>
                  <button
                    type="button"
                    className={[
                      "mdc-admin-skills__list-item",
                      selectedId === skill.id && !isCreating ? "is-selected" : "",
                      !skill.isActive ? "is-inactive" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() => selectSkill(skill)}
                  >
                    <Sparkles size={16} aria-hidden="true" />
                    <span>
                      <strong>{skill.label}</strong>
                      <small>{skill.skillKey}</small>
                    </span>
                    {!skill.isActive ? <em>Inativa</em> : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="mdc-admin-split__main mdc-admin-panel mdc-admin-skills__editor">
          {!canManage ? (
            <p className="mdc-admin-skills__muted">
              Você não tem permissão para gerenciar skills (`minha-delpi.chat.tools.manage`).
            </p>
          ) : !isCreating && !selectedSkill ? (
            <p className="mdc-admin-skills__muted">
              Selecione uma skill na lista ou crie uma nova.
            </p>
          ) : (
            <form className="mdc-admin-skills__form" onSubmit={(event) => void handleSave(event)}>
              <h3>{isCreating ? "Nova skill" : `Editar — ${selectedSkill?.label}`}</h3>

              <div className="mdc-admin-skills__form-grid">
                <label className="mdc-admin-field">
                  <span>Chave (slug)</span>
                  <input
                    value={draft.skillKey}
                    disabled={!isCreating || isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({ ...current, skillKey: event.target.value }))
                    }
                    placeholder="ex.: sql, resumo-executivo"
                    required
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Nome exibido</span>
                  <input
                    value={draft.label}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({ ...current, label: event.target.value }))
                    }
                    required
                  />
                </label>

                <label className="mdc-admin-field mdc-admin-skills__field-span">
                  <span>Descrição (UI)</span>
                  <textarea
                    value={draft.description}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({ ...current, description: event.target.value }))
                    }
                    rows={3}
                  />
                </label>

                <label className="mdc-admin-field mdc-admin-skills__field-span">
                  <span>Policy (Markdown para o LLM)</span>
                  <textarea
                    value={draft.policyContent}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({ ...current, policyContent: event.target.value }))
                    }
                    rows={12}
                    placeholder="Instruções injetadas no contexto quando a skill estiver ativa no agente."
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Arquivo policy (fallback)</span>
                  <input
                    value={draft.policyFile}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({ ...current, policyFile: event.target.value }))
                    }
                    placeholder="sql-assistant-skill.md"
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Flag no metadata</span>
                  <input
                    value={draft.metadataFlag}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({ ...current, metadataFlag: event.target.value }))
                    }
                    placeholder="authoring"
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Flag legada (opcional)</span>
                  <input
                    value={draft.legacyMetadataFlag}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({
                        ...current,
                        legacyMetadataFlag: event.target.value,
                      }))
                    }
                    placeholder="sqlAuthoring"
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Dica de execução</span>
                  <input
                    value={draft.executionPathHint}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({
                        ...current,
                        executionPathHint: event.target.value,
                      }))
                    }
                    placeholder="POST /data/sql"
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Chave derivada</span>
                  <input
                    value={draft.executionDerivedKey}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({
                        ...current,
                        executionDerivedKey: event.target.value,
                      }))
                    }
                    placeholder="sqlExecutionAvailable"
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Ordem</span>
                  <input
                    type="number"
                    value={draft.sortOrder}
                    disabled={isSaving}
                    onChange={(event) =>
                      setDraft((current) => ({
                        ...current,
                        sortOrder: Number(event.target.value),
                      }))
                    }
                  />
                </label>
              </div>

              <AdminFormCheckbox
                title="Skill ativa no catálogo"
                hint="Skills inativas não aparecem para novos vínculos em agentes."
                checked={draft.isActive}
                disabled={isSaving}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, isActive: event.target.checked }))
                }
              />

              <div className="mdc-admin-skills__form-actions">
                <button
                  type="submit"
                  className="mdc-admin-btn mdc-admin-btn--primary"
                  disabled={isSaving}
                >
                  {isSaving ? "Salvando…" : isCreating ? "Criar skill" : "Salvar alterações"}
                </button>

                {!isCreating && selectedId ? (
                  <button
                    type="button"
                    className="mdc-admin-btn mdc-admin-btn--danger"
                    disabled={isSaving}
                    onClick={() => void handleDeactivate()}
                  >
                    <Trash2 size={15} aria-hidden="true" />
                    <span>Desativar</span>
                  </button>
                ) : null}
              </div>
            </form>
          )}

          {error ? (
            <p className="mdc-admin-skills__error" role="alert">
              {error}
            </p>
          ) : null}
          {success ? <p className="mdc-admin-skills__success">{success}</p> : null}
        </div>
      </div>
    </section>
  );
}
