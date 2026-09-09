import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

import { ChatAdminNativeTextField } from "../shared/chatAdminFormFields";

import "./KnowledgeCuratorialFields.css";

type KnowledgeCuratorialFieldsProps = {
  category: string;
  tags: string;
  namespace: string;
  domain: string;
  priority: string;
  qualityScore: string;
  disabled?: boolean;
  idPrefix?: string;
  onCategoryChange: (value: string) => void;
  onTagsChange: (value: string) => void;
  onNamespaceChange: (value: string) => void;
  onDomainChange: (value: string) => void;
  onPriorityChange: (value: string) => void;
  onQualityScoreChange: (value: string) => void;
};

export function KnowledgeCuratorialFields({
  category,
  tags,
  namespace,
  domain,
  priority,
  qualityScore,
  disabled = false,
  idPrefix = "knowledge-curatorial",
  onCategoryChange,
  onTagsChange,
  onNamespaceChange,
  onDomainChange,
  onPriorityChange,
  onQualityScoreChange,
}: KnowledgeCuratorialFieldsProps) {
  const fields = ADMIN_HELP.fields.documents;

  return (
    <div className="mdc-knowledge-curatorial">
      <div className="mdc-knowledge-curatorial__grid">
        <ChatAdminNativeTextField
          id={`${idPrefix}-category`}
          label="Categoria"
          hint={fields.category}
          value={category}
          disabled={disabled}
          placeholder="Ex.: atendimento"
          onChange={onCategoryChange}
        />
        <ChatAdminNativeTextField
          id={`${idPrefix}-namespace`}
          label="Namespace"
          hint={fields.namespace}
          value={namespace}
          disabled={disabled}
          placeholder="Ex.: global:rh"
          onChange={onNamespaceChange}
        />
        <ChatAdminNativeTextField
          id={`${idPrefix}-domain`}
          label="Domínio"
          hint={fields.domain}
          value={domain}
          disabled={disabled}
          placeholder="Ex.: recursos-humanos"
          onChange={onDomainChange}
        />
        <ChatAdminNativeTextField
          id={`${idPrefix}-priority`}
          label="Prioridade (1-5)"
          hint={fields.priority}
          type="number"
          min={1}
          max={5}
          value={priority}
          disabled={disabled}
          onChange={onPriorityChange}
        />
        <ChatAdminNativeTextField
          id={`${idPrefix}-quality`}
          label="Pontuação de qualidade (0-100)"
          hint={fields.qualityScore}
          type="number"
          min={0}
          max={100}
          value={qualityScore}
          disabled={disabled}
          onChange={onQualityScoreChange}
        />
      </div>

      <ChatAdminNativeTextField
        id={`${idPrefix}-tags`}
        label="Tags (vírgula)"
        hint={fields.tags}
        value={tags}
        disabled={disabled}
        placeholder="Ex.: onboarding, faq"
        onChange={onTagsChange}
      />
    </div>
  );
}
