import { ChatNativeTextInput } from "../../shared/chatNativeFormFields";
import "./KnowledgeCuratorialFields.css";

type KnowledgeCuratorialFieldsProps = {
  category: string;
  tags: string;
  namespace: string;
  domain: string;
  priority: string;
  qualityScore: string;
  disabled?: boolean;
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
  onCategoryChange,
  onTagsChange,
  onNamespaceChange,
  onDomainChange,
  onPriorityChange,
  onQualityScoreChange,
}: KnowledgeCuratorialFieldsProps) {
  return (
    <div className="mdc-knowledge-curatorial">
      <div className="mdc-knowledge-curatorial__grid">
        <label className="mdc-admin-field">
          <span>Categoria</span>
          <ChatNativeTextInput
            value={category}
            disabled={disabled}
            placeholder="Ex.: atendimento"
            onChange={(event) => onCategoryChange(event.target.value)}
          />
        </label>

        <label className="mdc-admin-field">
          <span>Namespace</span>
          <ChatNativeTextInput
            value={namespace}
            disabled={disabled}
            placeholder="Ex.: global:rh"
            onChange={(event) => onNamespaceChange(event.target.value)}
          />
        </label>

        <label className="mdc-admin-field">
          <span>Domínio</span>
          <ChatNativeTextInput
            value={domain}
            disabled={disabled}
            placeholder="Ex.: recursos-humanos"
            onChange={(event) => onDomainChange(event.target.value)}
          />
        </label>

        <label className="mdc-admin-field">
          <span>Prioridade (1-5)</span>
          <ChatNativeTextInput
            type="number"
            min={1}
            max={5}
            value={priority}
            disabled={disabled}
            onChange={(event) => onPriorityChange(event.target.value)}
          />
        </label>

        <label className="mdc-admin-field">
          <span>Pontuação de qualidade (0-100)</span>
          <ChatNativeTextInput
            type="number"
            min={0}
            max={100}
            value={qualityScore}
            disabled={disabled}
            onChange={(event) => onQualityScoreChange(event.target.value)}
          />
        </label>
      </div>

      <label className="mdc-admin-field">
        <span>Tags (vírgula)</span>
        <ChatNativeTextInput
          value={tags}
          disabled={disabled}
          placeholder="Ex.: onboarding, faq"
          onChange={(event) => onTagsChange(event.target.value)}
        />
      </label>
    </div>
  );
}
