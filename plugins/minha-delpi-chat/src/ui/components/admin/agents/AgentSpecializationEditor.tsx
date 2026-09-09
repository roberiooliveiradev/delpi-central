import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useState } from "react";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import {
  getAdminAgentSpecialization,
  listAdminAgentSpecializationPresets,
  saveAdminAgentSpecialization,
} from "../../../../data/api/adminApi";
import type {
  AdminAgentSpecialization,
  AdminAgentSpecializationPreset,
} from "../../../../data/api/adminTypes";
import {
  ChatAdminNativeSelectField,
  ChatAdminNativeTextField,
} from "../shared/chatAdminFormFields";

const EMPTY_SPECIALIZATION: AdminAgentSpecialization = {
  enabled: true,
  presetKey: "",
  label: "",
  domain: "",
  knowledgeDomains: [],
  knowledgeNamespaces: [],
  knowledgeCategories: [],
  knowledgeTags: [],
  guidelineCategories: [],
  allowedTools: [],
  includeGlobalKnowledge: true,
};

type AgentSpecializationEditorProps = {
  agentId: string;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  /** Prefixo de ids de campo para evitar colisão quando há duas instâncias. */
  fieldIdPrefix?: string;
  className?: string;
  onSaved?: () => void;
};

type ListFieldKey =
  | "knowledgeDomains"
  | "knowledgeNamespaces"
  | "knowledgeCategories"
  | "knowledgeTags"
  | "guidelineCategories"
  | "allowedTools";

/**
 * Formulário canônico de especialização RAG/tools por agente.
 * Usado no Studio (builder) e no catálogo admin — mesma API, sem segundo CRUD.
 */
export function AgentSpecializationEditor({
  agentId,
  getAccessToken,
  fieldIdPrefix = "agent-spec",
  className,
  onSaved,
}: AgentSpecializationEditorProps) {
  const [presets, setPresets] = useState<AdminAgentSpecializationPreset[]>([]);
  const [form, setForm] = useState<AdminAgentSpecialization>(EMPTY_SPECIALIZATION);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const [presetsResponse, specializationResponse] = await Promise.all([
        listAdminAgentSpecializationPresets({ getAccessToken }),
        getAdminAgentSpecialization(agentId, { getAccessToken }),
      ]);

      setPresets(presetsResponse.presets);
      const specialization = specializationResponse.specialization;
      setForm(
        specialization
          ? {
              ...EMPTY_SPECIALIZATION,
              ...specialization,
              knowledgeDomains: specialization.knowledgeDomains ?? [],
              knowledgeNamespaces: specialization.knowledgeNamespaces ?? [],
              knowledgeCategories: specialization.knowledgeCategories ?? [],
              knowledgeTags: specialization.knowledgeTags ?? [],
              guidelineCategories: specialization.guidelineCategories ?? [],
              allowedTools: specialization.allowedTools ?? [],
            }
          : { ...EMPTY_SPECIALIZATION, enabled: false },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar especialização.");
      setForm(EMPTY_SPECIALIZATION);
    } finally {
      setIsLoading(false);
    }
  }, [agentId, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  function applyPreset(presetKey: string) {
    const preset = presets.find((item) => item.key === presetKey);

    if (!preset) {
      return;
    }

    setForm((current) => ({
      ...current,
      enabled: true,
      presetKey: preset.key,
      label: preset.label,
      domain: preset.domain,
      knowledgeDomains: preset.knowledgeDomains ?? [],
      knowledgeNamespaces: preset.knowledgeNamespaces ?? [],
      knowledgeCategories: preset.knowledgeCategories ?? [],
      knowledgeTags: preset.knowledgeTags ?? [],
      guidelineCategories: preset.guidelineCategories ?? [],
      allowedTools: preset.allowedTools ?? [],
      includeGlobalKnowledge: preset.includeGlobalKnowledge ?? true,
    }));
  }

  function updateListField(key: ListFieldKey, value: string) {
    setForm((current) => ({
      ...current,
      [key]: value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    }));
  }

  async function handleSave() {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await saveAdminAgentSpecialization(
        {
          specialization: form.enabled ? form : { enabled: false },
        },
        agentId,
        { getAccessToken },
      );
      setSuccessMessage("Especialização do agente salva.");
      onSaved?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar especialização.");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return <p className="mdc-chat-muted">Carregando especialização…</p>;
  }

  return (
    <div className={className ?? "mdc-admin-agents__editor-fields"}>
      {error ? <p className="mdc-admin-agents__error">{error}</p> : null}
      {successMessage ? <p className="mdc-admin-agents__success">{successMessage}</p> : null}

      <NativeCheckboxControl
        className="mdc-admin-agents__toggle"
        checked={form.enabled}
        label="Especialização ativa"
        hint={ADMIN_HELP.fields.specialization.enabled}
        hintPlacement="tooltip"
        hintAriaLabel="Ajuda: Especialização ativa"
        onChange={(enabled) => setForm((current) => ({ ...current, enabled }))}
      />

      {form.enabled ? (
        <>
          <ChatAdminNativeSelectField
            id={`${fieldIdPrefix}-preset`}
            label="Preset de domínio"
            hint={ADMIN_HELP.fields.specialization.preset}
            span={false}
            value={form.presetKey ?? ""}
            placeholderOption="Personalizado"
            options={presets.map((preset) => ({
              value: preset.key,
              label: preset.label,
            }))}
            onChange={(value) => {
              setForm((current) => ({ ...current, presetKey: value }));
              if (value) {
                applyPreset(value);
              }
            }}
          />

          <div className="mdc-admin-agents__grid">
            <ChatAdminNativeTextField
              id={`${fieldIdPrefix}-label`}
              label="Rótulo"
              hint={ADMIN_HELP.fields.specialization.label}
              value={form.label ?? ""}
              onChange={(value) => setForm((current) => ({ ...current, label: value }))}
            />
            <ChatAdminNativeTextField
              id={`${fieldIdPrefix}-domain`}
              label="Domínio"
              hint={ADMIN_HELP.fields.specialization.domain}
              value={form.domain ?? ""}
              onChange={(value) => setForm((current) => ({ ...current, domain: value }))}
            />
          </div>

          <ChatAdminNativeTextField
            id={`${fieldIdPrefix}-knowledge-domains`}
            label="Domínios de conhecimento (vírgula)"
            hint={ADMIN_HELP.fields.specialization.knowledgeDomains}
            value={(form.knowledgeDomains ?? []).join(", ")}
            onChange={(value) => updateListField("knowledgeDomains", value)}
          />

          <ChatAdminNativeTextField
            id={`${fieldIdPrefix}-namespaces`}
            label="Namespaces (vírgula)"
            hint={ADMIN_HELP.fields.specialization.namespaces}
            value={(form.knowledgeNamespaces ?? []).join(", ")}
            onChange={(value) => updateListField("knowledgeNamespaces", value)}
          />

          <ChatAdminNativeTextField
            id={`${fieldIdPrefix}-knowledge-categories`}
            label="Categorias de conhecimento (vírgula)"
            hint={ADMIN_HELP.fields.specialization.knowledgeCategories}
            value={(form.knowledgeCategories ?? []).join(", ")}
            onChange={(value) => updateListField("knowledgeCategories", value)}
          />

          <ChatAdminNativeTextField
            id={`${fieldIdPrefix}-knowledge-tags`}
            label="Tags de conhecimento (vírgula)"
            hint={ADMIN_HELP.fields.specialization.knowledgeTags}
            value={(form.knowledgeTags ?? []).join(", ")}
            onChange={(value) => updateListField("knowledgeTags", value)}
          />

          <ChatAdminNativeTextField
            id={`${fieldIdPrefix}-guideline-categories`}
            label="Categorias de diretrizes (vírgula)"
            hint={ADMIN_HELP.fields.specialization.guidelineCategories}
            value={(form.guidelineCategories ?? []).join(", ")}
            onChange={(value) => updateListField("guidelineCategories", value)}
          />

          <ChatAdminNativeTextField
            id={`${fieldIdPrefix}-allowed-tools`}
            label="Tools permitidas (vírgula)"
            hint={ADMIN_HELP.fields.specialization.allowedTools}
            value={(form.allowedTools ?? []).join(", ")}
            onChange={(value) => updateListField("allowedTools", value)}
          />

          <NativeCheckboxControl
            className="mdc-admin-agents__toggle"
            checked={form.includeGlobalKnowledge ?? true}
            label="Incluir base global além do domínio"
            hint={ADMIN_HELP.fields.specialization.includeGlobal}
            hintPlacement="tooltip"
            hintAriaLabel="Ajuda: Incluir base global"
            onChange={(includeGlobalKnowledge) =>
              setForm((current) => ({ ...current, includeGlobalKnowledge }))
            }
          />
        </>
      ) : null}

      <button
        type="button"
        className="mdc-admin-btn mdc-admin-btn--primary"
        disabled={isSaving}
        onClick={() => void handleSave()}
      >
        {isSaving ? "Salvando..." : "Salvar especialização"}
      </button>
    </div>
  );
}
