import { useEffect, useState } from "react";

import {
  listFollowupTemplates,
  listRequestTypes,
  type CatalogItem,
  type TemplateCatalogItem,
} from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import { HelpdeskSelect } from "../ui/helpdeskUi";

export type TicketReplyMetaState = {
  templateId: number | null;
  requestTypeId: number | null;
};

export const EMPTY_TICKET_REPLY_META: TicketReplyMetaState = {
  templateId: null,
  requestTypeId: null,
};

type Props = {
  value: TicketReplyMetaState;
  onChange: (next: TicketReplyMetaState) => void;
  /** Called when a template should replace rich-text content. */
  onApplyContent?: (content: string) => void;
  disabled?: boolean;
};

function catalogOptions(items: CatalogItem[]) {
  return items.map((item) => ({ value: String(item.id), label: item.name }));
}

/** Followup secondary fields — template + request source (HLAPI PROVEN). */
export function TicketReplyActionFields({ value, onChange, onApplyContent, disabled }: Props) {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([]);
  const [requestTypes, setRequestTypes] = useState<CatalogItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listFollowupTemplates(), listRequestTypes()])
      .then(([tpl, types]) => {
        if (cancelled) return;
        setTemplates(tpl);
        setRequestTypes(types);
        setLoaded(true);
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError("Não foi possível carregar opções da resposta.");
          setLoaded(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function patch(partial: Partial<TicketReplyMetaState>) {
    onChange({ ...value, ...partial });
  }

  function applyTemplate(templateId: number | null) {
    if (templateId == null) {
      patch({ templateId: null });
      return;
    }
    const template = templates.find((item) => item.id === templateId);
    if (!template) {
      patch({ templateId });
      return;
    }
    patch({
      templateId,
      requestTypeId: template.request_type_id ?? value.requestTypeId,
    });
    if (template.content) onApplyContent?.(template.content);
  }

  const help = helpTooltips.detailUi.actionFields.reply;

  return (
    <div className="helpdesk-action-fields helpdesk-action-fields--reply">
      {loadError ? <p className="helpdesk-action-fields__error">{loadError}</p> : null}
      <div className="helpdesk-action-fields__grid">
        {loaded && templates.length > 0 ? (
          <HelpdeskSelect
            label="Modelo"
            hint={help.model}
            value={value.templateId != null ? String(value.templateId) : ""}
            onChange={(next) => applyTemplate(next ? Number(next) : null)}
            options={[{ value: "", label: "Sem modelo" }, ...catalogOptions(templates)]}
            disabled={disabled}
          />
        ) : null}
        {loaded && requestTypes.length > 0 ? (
          <HelpdeskSelect
            label="Origem"
            hint={help.source}
            value={value.requestTypeId != null ? String(value.requestTypeId) : ""}
            onChange={(next) => patch({ requestTypeId: next ? Number(next) : null })}
            options={[{ value: "", label: "Sem origem" }, ...catalogOptions(requestTypes)]}
            disabled={disabled}
          />
        ) : null}
      </div>
    </div>
  );
}
