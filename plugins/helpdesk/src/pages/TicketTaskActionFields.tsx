import { useEffect, useState } from "react";
import { FieldLabel } from "@delpi/plugin-ui/index";

import {
  listGroups,
  listTaskCategories,
  listTaskStatuses,
  listTaskTemplates,
  type CatalogItem,
  type TemplateCatalogItem,
  type TicketTaskCreateBody,
} from "../api/helpdeskApi";
import { helpTooltips } from "../content/helpTooltips";
import {
  HelpdeskAssigneePicker,
  type HelpdeskAssigneeValue,
} from "../components/HelpdeskAssigneePicker";
import { HelpdeskSelect } from "../ui/helpdeskUi";

export type TicketTaskFormState = {
  content: string;
  templateId: number | null;
  state: number | null;
  durationMinutes: number | null;
  categoryId: number | null;
  assignee: HelpdeskAssigneeValue | null;
  groupTechId: number | null;
  planEnabled: boolean;
  plannedBegin: string;
  plannedEnd: string;
};

export const EMPTY_TICKET_TASK_FORM: TicketTaskFormState = {
  content: "",
  templateId: null,
  state: 1,
  durationMinutes: null,
  categoryId: null,
  assignee: null,
  groupTechId: null,
  planEnabled: false,
  plannedBegin: "",
  plannedEnd: "",
};

export function ticketTaskFormToBody(form: TicketTaskFormState): TicketTaskCreateBody {
  const body: TicketTaskCreateBody = { content: form.content };
  if (form.state != null) body.state = form.state;
  if (form.durationMinutes != null && form.durationMinutes >= 0) {
    body.duration_seconds = Math.round(form.durationMinutes * 60);
  }
  if (form.categoryId != null) body.category_id = form.categoryId;
  if (form.assignee?.id) {
    const techId = Number(form.assignee.id);
    if (Number.isFinite(techId) && techId > 0) body.user_tech_id = techId;
  }
  if (form.groupTechId != null) body.group_tech_id = form.groupTechId;
  if (form.planEnabled && form.plannedBegin.trim()) {
    body.planned_begin = toProviderDateTime(form.plannedBegin);
  }
  if (form.planEnabled && form.plannedEnd.trim()) {
    body.planned_end = toProviderDateTime(form.plannedEnd);
  }
  return body;
}

function toProviderDateTime(localValue: string): string {
  const trimmed = localValue.trim();
  if (!trimmed) return "";
  return trimmed.length === 16 ? `${trimmed}:00` : trimmed;
}

function catalogOptions(items: CatalogItem[]) {
  return items.map((item) => ({ value: String(item.id), label: item.name }));
}

type Props = {
  value: TicketTaskFormState;
  onChange: (next: TicketTaskFormState) => void;
  disabled?: boolean;
};

/** Action-specific task fields (HLAPI TicketTask PROVEN subset). */
export function TicketTaskActionFields({ value, onChange, disabled }: Props) {
  const [templates, setTemplates] = useState<TemplateCatalogItem[]>([]);
  const [categories, setCategories] = useState<CatalogItem[]>([]);
  const [statuses, setStatuses] = useState<CatalogItem[]>([]);
  const [groups, setGroups] = useState<CatalogItem[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listTaskTemplates(),
      listTaskCategories(),
      listTaskStatuses(),
      listGroups(),
    ])
      .then(([tpl, cats, sts, grps]) => {
        if (cancelled) return;
        setTemplates(tpl);
        setCategories(cats);
        setStatuses(sts);
        setGroups(grps);
        setLoaded(true);
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError("Não foi possível carregar opções da tarefa.");
          setLoaded(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function patch(partial: Partial<TicketTaskFormState>) {
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
      state: template.state ?? value.state,
      durationMinutes:
        template.duration_seconds != null
          ? Math.round(template.duration_seconds / 60)
          : value.durationMinutes,
      categoryId: template.category_id ?? value.categoryId,
      assignee:
        template.user_tech_id != null
          ? {
              id: String(template.user_tech_id),
              name: value.assignee?.name || `Usuário ${template.user_tech_id}`,
              email: value.assignee?.email || "",
            }
          : value.assignee,
      groupTechId: template.group_tech_id ?? value.groupTechId,
    });
  }

  const help = helpTooltips.detailUi.actionFields.task;

  return (
    <div className="helpdesk-action-fields helpdesk-action-fields--task">
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
        {loaded && categories.length > 0 ? (
          <HelpdeskSelect
            label="Categoria"
            hint={help.category}
            value={value.categoryId != null ? String(value.categoryId) : ""}
            onChange={(next) => patch({ categoryId: next ? Number(next) : null })}
            options={[{ value: "", label: "Sem categoria" }, ...catalogOptions(categories)]}
            disabled={disabled}
          />
        ) : null}
        {loaded && statuses.length > 0 ? (
          <HelpdeskSelect
            label="Status"
            hint={help.status}
            value={value.state != null ? String(value.state) : ""}
            onChange={(next) => patch({ state: next === "" ? null : Number(next) })}
            options={catalogOptions(statuses)}
            disabled={disabled}
          />
        ) : null}
        <label className="helpdesk-action-fields__field">
          <FieldLabel label="Duração (minutos)" hint={help.duration} />
          <input
            type="number"
            min={0}
            step={1}
            value={value.durationMinutes ?? ""}
            disabled={disabled}
            onChange={(event) => {
              const raw = event.target.value;
              patch({ durationMinutes: raw === "" ? null : Math.max(0, Number(raw)) });
            }}
          />
        </label>
        <div className="helpdesk-action-fields__field">
          <HelpdeskAssigneePicker
            label="Técnico responsável"
            hint={help.assignee}
            value={value.assignee}
            onChange={(user) => patch({ assignee: user })}
            disabled={disabled}
            purpose="assignee"
            placeholder="Buscar técnico…"
            emptyLabel="Nenhum técnico selecionado"
          />
        </div>
        {loaded && groups.length > 0 ? (
          <HelpdeskSelect
            label="Grupo"
            hint={help.group}
            value={value.groupTechId != null ? String(value.groupTechId) : ""}
            onChange={(next) => patch({ groupTechId: next ? Number(next) : null })}
            options={[{ value: "", label: "Sem grupo" }, ...catalogOptions(groups)]}
            disabled={disabled}
          />
        ) : null}
      </div>
      <label className="helpdesk-action-fields__switch">
        <input
          type="checkbox"
          checked={value.planEnabled}
          disabled={disabled}
          onChange={(event) => patch({ planEnabled: event.target.checked })}
        />
        <FieldLabel label="Planejar esta tarefa" hint={help.planning} />
      </label>
      {value.planEnabled ? (
        <div className="helpdesk-action-fields__grid helpdesk-action-fields__grid--plan">
          <label className="helpdesk-action-fields__field">
            <FieldLabel label="Início" hint={help.planBegin} />
            <input
              type="datetime-local"
              value={value.plannedBegin}
              disabled={disabled}
              onChange={(event) => patch({ plannedBegin: event.target.value })}
            />
          </label>
          <label className="helpdesk-action-fields__field">
            <FieldLabel label="Fim" hint={help.planEnd} />
            <input
              type="datetime-local"
              value={value.plannedEnd}
              disabled={disabled}
              onChange={(event) => patch({ plannedEnd: event.target.value })}
            />
          </label>
        </div>
      ) : null}
    </div>
  );
}
