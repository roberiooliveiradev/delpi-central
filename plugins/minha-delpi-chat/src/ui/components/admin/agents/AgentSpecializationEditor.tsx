import { ChatNativeTextInput } from "../../shared/chatNativeFormFields";
import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useState } from "react";

import {
  getAdminAgentSpecialization,
  listAdminAgentSpecializationPresets,
  saveAdminAgentSpecialization,
} from "../../../../data/api/adminApi";
import type {
  AdminAgentSpecialization,
  AdminAgentSpecializationPreset,
} from "../../../../data/api/adminTypes";
import { ChatAdminNativeSelectField } from "../shared/chatAdminFormFields";

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
        onChange={(enabled) => setForm((current) => ({ ...current, enabled }))}
      />

      {form.enabled ? (
        <>
          <ChatAdminNativeSelectField
            id={`${fieldIdPrefix}-preset`}
            label="Preset de domínio"
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
            <label>
              <span>Rótulo</span>
              <ChatNativeTextInput
                value={form.label ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, label: event.target.value }))
                }
              />
            </label>
            <label>
              <span>Domínio</span>
              <ChatNativeTextInput
                value={form.domain ?? ""}
                onChange={(event) =>
                  setForm((current) => ({ ...current, domain: event.target.value }))
                }
              />
            </label>
          </div>

          <label>
            <span>Domínios de conhecimento (vírgula)</span>
            <ChatNativeTextInput
              value={(form.knowledgeDomains ?? []).join(", ")}
              onChange={(event) => updateListField("knowledgeDomains", event.target.value)}
            />
          </label>

          <label>
            <span>Namespaces (vírgula)</span>
            <ChatNativeTextInput
              value={(form.knowledgeNamespaces ?? []).join(", ")}
              onChange={(event) => updateListField("knowledgeNamespaces", event.target.value)}
            />
          </label>

          <label>
            <span>Categorias de conhecimento (vírgula)</span>
            <ChatNativeTextInput
              value={(form.knowledgeCategories ?? []).join(", ")}
              onChange={(event) => updateListField("knowledgeCategories", event.target.value)}
            />
          </label>

          <label>
            <span>Tags de conhecimento (vírgula)</span>
            <ChatNativeTextInput
              value={(form.knowledgeTags ?? []).join(", ")}
              onChange={(event) => updateListField("knowledgeTags", event.target.value)}
            />
          </label>

          <label>
            <span>Categorias de diretrizes (vírgula)</span>
            <ChatNativeTextInput
              value={(form.guidelineCategories ?? []).join(", ")}
              onChange={(event) => updateListField("guidelineCategories", event.target.value)}
            />
          </label>

          <label>
            <span>Tools permitidas (vírgula)</span>
            <ChatNativeTextInput
              value={(form.allowedTools ?? []).join(", ")}
              onChange={(event) => updateListField("allowedTools", event.target.value)}
            />
          </label>

          <NativeCheckboxControl
            className="mdc-admin-agents__toggle"
            checked={form.includeGlobalKnowledge ?? true}
            label="Incluir base global além do domínio"
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
