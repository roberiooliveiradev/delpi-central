import { useEffect, useState } from "react";

import {
  listSolutionTemplates,
  listSolutionTypes,
  type CatalogItem,
  type TemplateCatalogItem,
} from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import { HelpdeskSelect } from "../ui/helpdeskUi";

export type TicketSolutionFormState = {
  content: string;
  templateId: number | null;
  solutionTypeId: number | null;
};

export const EMPTY_TICKET_SOLUTION_FORM: TicketSolutionFormState = {
  content: "",
  templateId: null,
  solutionTypeId: null,
};

export function ticketSolutionFormToBody(form: TicketSolutionFormState): {
  content: string;
  solution_type_id?: number;
} {
  const body: { content: string; solution_type_id?: number } = { content: form.content };
  if (form.solutionTypeId != null) body.solution_type_id = form.solutionTypeId;
  return body;
}

type Props = {
  value: TicketSolutionFormState;
  onChange: (next: TicketSolutionFormState) => void;
  disabled?: boolean;
};

function catalogOptions(items: CatalogItem[]) {
  return items.map((item) => ({ value: String(item.id), label: item.name }));
}

/** Solution secondary fields — template + solution type (HLAPI PROVEN). */
export function TicketSolutionActionFields({ value, onChange, disabled }: Props) {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([]);
  const [types, setTypes] = useState<CatalogItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([listSolutionTemplates(), listSolutionTypes()])
      .then(([tpl, typeRows]) => {
        if (cancelled) return;
        setTemplates(tpl);
        setTypes(typeRows);
        setLoaded(true);
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError("Não foi possível carregar opções da solução.");
          setLoaded(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function patch(partial: Partial<TicketSolutionFormState>) {
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
      content: template.content || value.content,
      solutionTypeId: template.solution_type_id ?? value.solutionTypeId,
    });
  }

  const help = helpTooltips.detailUi.actionFields.solution;

  return (
    <div className="helpdesk-action-fields helpdesk-action-fields--solution">
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
        {loaded && types.length > 0 ? (
          <HelpdeskSelect
            label="Tipo da solução"
            hint={help.type}
            value={value.solutionTypeId != null ? String(value.solutionTypeId) : ""}
            onChange={(next) => patch({ solutionTypeId: next ? Number(next) : null })}
            options={[{ value: "", label: "Sem tipo" }, ...catalogOptions(types)]}
            disabled={disabled}
          />
        ) : null}
      </div>
    </div>
  );
}
