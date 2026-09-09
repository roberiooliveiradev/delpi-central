import { HintAction } from "@delpi/plugin-ui/index";
import { ExternalLink, Plus, RefreshCw, Sparkles, Trash2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createAdminChatSkill,
  deactivateAdminChatSkill,
  listAdminChatSkills,
  updateAdminChatSkill,
} from "../../../../data/api/adminApi";
import type { AdminChatSkill, AdminRbacSummary } from "../../../../data/api/adminTypes";
import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import { buildChatAgentHref } from "../../../../navigation/chatRoutes";
import { navigateChatHref } from "../../../../navigation/chatNavigation";
import { AdminFormCheckbox } from "../shared/AdminFormCheckbox";
import {
  ChatAdminNativeTextAreaField,
  ChatAdminNativeTextField,
} from "../shared/chatAdminFormFields";
import { useConfirmDialog } from "../../shared";
import { AdminTabHeader } from "../shared/AdminTabHeader";
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
      <AdminTabHeader
        className="mdc-admin-skills__toolbar"
        eyebrow="Conhecimento"
        title="Comportamentos"
        description="Catálogo global de skills de prompt. Skills e actions por agente são editadas no Studio — não neste CRUD."
        helpHint={ADMIN_HELP.pages.behaviors}
        summary={
          <SkillsSummaryStrip
            summary={summary}
            activeFilter={statusFilter}
            isLoading={isLoading}
            onFilterChange={setStatusFilter}
          />
        }
        actions={
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
            <HintAction hint={ADMIN_HELP.fields.skills.openStudio} ariaLabel="Ajuda: Abrir Studio">
              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn"
                onClick={() => navigateChatHref(buildChatAgentHref(null))}
              >
                <ExternalLink size={15} aria-hidden="true" />
                <span>Abrir Studio</span>
              </button>
            </HintAction>
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
        }
      />

      <aside className="mdc-admin-skills__studio-callout" aria-label="Skills globais versus Studio">
        <p>
          Este catálogo define comportamentos <strong>globais</strong> reutilizáveis. Para
          ativar skills em um agente, editar prompt ou actions, use o{" "}
          <button
            type="button"
            className="mdc-admin-skills__studio-link"
            onClick={() => navigateChatHref(buildChatAgentHref(null))}
          >
            Studio do agente
          </button>
          .
        </p>
      </aside>

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
                <ChatAdminNativeTextField
                  id="admin-skill-key"
                  label="Chave (slug)"
                  hint={ADMIN_HELP.fields.skills.key}
                  value={draft.skillKey}
                  disabled={!isCreating || isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({ ...current, skillKey: value }))
                  }
                  placeholder="ex.: sql, resumo-executivo"
                  required
                />

                <ChatAdminNativeTextField
                  id="admin-skill-label"
                  label="Nome exibido"
                  hint={ADMIN_HELP.fields.skills.label}
                  value={draft.label}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({ ...current, label: value }))
                  }
                  required
                />

                <ChatAdminNativeTextAreaField
                  id="admin-skill-description"
                  label="Descrição (UI)"
                  hint={ADMIN_HELP.fields.skills.description}
                  className="mdc-admin-skills__field-span"
                  value={draft.description}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({ ...current, description: value }))
                  }
                  rows={3}
                />

                <ChatAdminNativeTextAreaField
                  id="admin-skill-policy"
                  label="Policy (Markdown para o LLM)"
                  hint={ADMIN_HELP.fields.skills.policyMarkdown}
                  className="mdc-admin-skills__field-span"
                  value={draft.policyContent}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({ ...current, policyContent: value }))
                  }
                  rows={12}
                  placeholder="Instruções injetadas no contexto quando a skill estiver ativa no agente."
                />

                <ChatAdminNativeTextField
                  id="admin-skill-policy-file"
                  label="Arquivo policy (fallback)"
                  hint={ADMIN_HELP.fields.skills.policyFile}
                  value={draft.policyFile}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({ ...current, policyFile: value }))
                  }
                  placeholder="sql-assistant-skill.md"
                />

                <ChatAdminNativeTextField
                  id="admin-skill-metadata-flag"
                  label="Flag no metadata"
                  hint={ADMIN_HELP.fields.skills.metadataFlag}
                  value={draft.metadataFlag}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({ ...current, metadataFlag: value }))
                  }
                />

                <ChatAdminNativeTextField
                  id="admin-skill-legacy-flag"
                  label="Flag legada (opcional)"
                  hint={ADMIN_HELP.fields.skills.legacyFlag}
                  value={draft.legacyMetadataFlag}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({
                      ...current,
                      legacyMetadataFlag: value,
                    }))
                  }
                />

                <ChatAdminNativeTextField
                  id="admin-skill-execution-hint"
                  label="Dica de execução"
                  hint={ADMIN_HELP.fields.skills.executionHint}
                  value={draft.executionPathHint}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({
                      ...current,
                      executionPathHint: value,
                    }))
                  }
                />

                <ChatAdminNativeTextField
                  id="admin-skill-derived-key"
                  label="Chave derivada"
                  hint={ADMIN_HELP.fields.skills.derivedKey}
                  value={draft.executionDerivedKey}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({
                      ...current,
                      executionDerivedKey: value,
                    }))
                  }
                  placeholder="sqlExecutionAvailable"
                />

                <ChatAdminNativeTextField
                  id="admin-skill-sort-order"
                  label="Ordem"
                  hint={ADMIN_HELP.fields.skills.sortOrder}
                  type="number"
                  value={String(draft.sortOrder)}
                  disabled={isSaving}
                  onChange={(value) =>
                    setDraft((current) => ({
                      ...current,
                      sortOrder: Number(value),
                    }))
                  }
                />
              </div>

              <AdminFormCheckbox
                title="Skill ativa no catálogo"
                hint={ADMIN_HELP.fields.skills.active}
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
