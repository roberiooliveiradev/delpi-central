import { useEffect, useState } from "react";
import { FieldLabel } from "@delpi/plugin-ui/index";

import {
  listGroups,
  listValidationTemplates,
  type CatalogItem,
  type TemplateCatalogItem,
} from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
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
  /** Shown when submit is blocked for missing group selection. */
  groupRequiredHint?: string | null;
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
  groupRequiredHint,
}: Props) {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([]);
  const [groups, setGroups] = useState<CatalogItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listValidationTemplates(), listGroups()])
      .then(([tpl, grps]) => {
        if (cancelled) return;
        setTemplates(tpl);
        setGroups(grps);
        setLoaded(true);
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError("Não foi possível carregar opções de aprovação.");
          setLoaded(true);
        }
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

  const help = helpTooltips.detailUi.actionFields.approval;

  return (
    <div className="helpdesk-action-fields helpdesk-action-fields--approval">
      {loadError ? <p className="helpdesk-action-fields__error">{loadError}</p> : null}
      <div className="helpdesk-action-fields__grid">
        {loaded && templates.length > 0 ? (
          <HelpdeskSelect
            label="Modelo"
            hint={help.model}
            value={templateId != null ? String(templateId) : ""}
            onChange={(next) => applyTemplate(next ? Number(next) : null)}
            options={[
              { value: "", label: "Sem modelo" },
              ...templates.map((item) => ({ value: String(item.id), label: item.name })),
            ]}
            disabled={disabled}
          />
        ) : null}
        <div className="helpdesk-action-fields__field">
          <FieldLabel label="Tipo de aprovador" hint={help.approverType} />
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
          loaded && groups.length > 0 ? (
            <div className="helpdesk-action-fields__field">
              <HelpdeskSelect
                label="Grupo aprovador"
                hint={help.group}
                value={groupId != null ? String(groupId) : ""}
                onChange={(next) => onGroupIdChange(next ? Number(next) : null)}
                options={[
                  { value: "", label: "Nenhum grupo selecionado" },
                  ...groups.map((item) => ({ value: String(item.id), label: item.name })),
                ]}
                disabled={disabled}
                required
              />
              {groupRequiredHint ? (
                <p className="helpdesk-action-fields__hint" role="status">
                  {groupRequiredHint}
                </p>
              ) : null}
            </div>
          ) : loaded ? (
            <p className="helpdesk-action-fields__error" role="status">
              Nenhum grupo disponível para aprovação.
            </p>
          ) : null
        ) : null}
      </div>
    </div>
  );
}
