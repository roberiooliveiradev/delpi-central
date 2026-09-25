import { useEffect, useState } from "react";

import {
  listGroups,
  listValidationTemplates,
  type CatalogItem,
  type TemplateCatalogItem,
} from "../api/helpdeskApi";
import { HelpdeskSegmentToggle, HelpdeskSelect } from "../ui/helpdeskUi";

export type ApprovalApproverType = "user" | "group";

type Props = {
  templateId: number | null;
  onTemplateIdChange: (id: number | null) => void;
  approverType: ApprovalApproverType;
  onApproverTypeChange: (next: ApprovalApproverType) => void;
  groupId: number | null;
  onGroupIdChange: (id: number | null) => void;
  onApplyContent?: (content: string) => void;
  disabled?: boolean;
};

/** Approval template + approver target (User|Group). Step bind remains TO_INVENTORY. */
export function TicketApprovalActionFields({
  templateId,
  onTemplateIdChange,
  approverType,
  onApproverTypeChange,
  groupId,
  onGroupIdChange,
  onApplyContent,
  disabled,
}: Props) {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([]);
  const [groups, setGroups] = useState<CatalogItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listValidationTemplates(), listGroups()])
      .then(([tpl, grps]) => {
        if (cancelled) return;
        setTemplates(tpl);
        setGroups(grps);
      })
      .catch(() => {
        if (!cancelled) setLoadError("Não foi possível carregar opções de aprovação.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function applyTemplate(nextId: number | null) {
    onTemplateIdChange(nextId);
    if (nextId == null) return;
    const template = templates.find((item) => item.id === nextId);
    if (template?.content) onApplyContent?.(template.content);
  }

  return (
    <div className="helpdesk-action-fields helpdesk-action-fields--approval">
      {loadError ? <p className="helpdesk-action-fields__error">{loadError}</p> : null}
      <div className="helpdesk-action-fields__grid">
        <HelpdeskSelect
          label="Modelo"
          value={templateId != null ? String(templateId) : ""}
          onChange={(next) => applyTemplate(next ? Number(next) : null)}
          options={[
            { value: "", label: "Sem modelo" },
            ...templates.map((item) => ({ value: String(item.id), label: item.name })),
          ]}
          disabled={disabled}
        />
        <div className="helpdesk-action-fields__field">
          <span>Tipo de aprovador</span>
          <HelpdeskSegmentToggle
            ariaLabel="Tipo de aprovador"
            idPrefix="helpdesk-approval-approver-type"
            size="sm"
            widthMode="fill"
            value={approverType}
            onChange={(value) => {
              if (value === "user" || value === "group") onApproverTypeChange(value);
            }}
            options={[
              { value: "user", label: "Usuário" },
              { value: "group", label: "Grupo" },
            ]}
            disabled={disabled}
          />
        </div>
        {approverType === "group" ? (
          <HelpdeskSelect
            label="Grupo aprovador"
            value={groupId != null ? String(groupId) : ""}
            onChange={(next) => onGroupIdChange(next ? Number(next) : null)}
            options={[
              { value: "", label: "Selecione um grupo" },
              ...groups.map((item) => ({ value: String(item.id), label: item.name })),
            ]}
            disabled={disabled}
          />
        ) : null}
      </div>
    </div>
  );
}
