import { useEffect, useState } from "react";

import { listValidationTemplates, type TemplateCatalogItem } from "../api/helpdeskApi";
import { HelpdeskSelect } from "../ui/helpdeskUi";

type Props = {
  templateId: number | null;
  onTemplateIdChange: (id: number | null) => void;
  onApplyContent?: (content: string) => void;
  disabled?: boolean;
};

/** Approval template catalog — prefills comment only (step bind TO_INVENTORY). */
export function TicketApprovalActionFields({
  templateId,
  onTemplateIdChange,
  onApplyContent,
  disabled,
}: Props) {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listValidationTemplates()
      .then((rows) => {
        if (!cancelled) setTemplates(rows);
      })
      .catch(() => {
        if (!cancelled) setLoadError("Não foi possível carregar modelos de aprovação.");
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
    </div>
  );
}
