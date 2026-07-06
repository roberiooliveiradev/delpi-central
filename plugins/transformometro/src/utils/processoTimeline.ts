export type ProcessoAuditLogEntry = {
  audit_id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  user_id?: string | null;
  user_email?: string | null;
  user_name?: string | null;
  payload_json?: Record<string, unknown> | null;
  created_at: string;
};

export type ProcessoTimelineCategory =
  | "processo"
  | "instancia"
  | "revisao"
  | "medicao"
  | "investimento"
  | "vinculo";

export type ProcessoTimelineFilter = "all" | ProcessoTimelineCategory;

export type ProcessoTimelineEntry = {
  id: string;
  category: ProcessoTimelineCategory;
  title: string;
  detail?: string;
  meta?: string;
  occurredAt: string;
};

const ENTITY_LABELS: Record<string, string> = {
  processo: "Processo",
  processo_instancia: "Melhoria",
  revisao: "Revisão",
  medicao: "Medição",
  investimento: "Investimento",
  vinculo: "Vínculo de recurso",
};

const ACTION_LABELS: Record<string, string> = {
  create: "Criação",
  update: "Atualização",
  delete: "Exclusão",
  duplicate: "Duplicação",
  activate: "Ativação",
  upsert: "Registro",
  reajuste: "Reajuste",
  "decomposition.updated": "Mapeamento atualizado",
  "decomposition.scope.updated": "Escopo WBS atualizado",
  "decomposition.context.updated": "Contexto operacional atualizado",
  "decomposition.overlay.updated": "Overlay de mapeamento atualizado",
  "diagram.macro.updated": "Diagrama macro atualizado",
  "diagram.macro.imported_bpmn": "Diagrama importado (BPMN)",
  "diagram.escopo.updated": "Diagrama de escopo atualizado",
  "diagram.overlay.updated": "Diagrama da revisão atualizado",
};

export const PROCESSO_TIMELINE_FILTER_OPTIONS: Array<{
  value: ProcessoTimelineFilter;
  label: string;
}> = [
  { value: "all", label: "Todos" },
  { value: "processo", label: "Processo" },
  { value: "instancia", label: "Melhorias" },
  { value: "revisao", label: "Revisões" },
  { value: "medicao", label: "Medição" },
  { value: "investimento", label: "Investimentos" },
  { value: "vinculo", label: "Recursos" },
];

function categoryForEntityType(entityType: string): ProcessoTimelineCategory {
  switch (entityType) {
    case "processo_instancia":
      return "instancia";
    case "revisao":
      return "revisao";
    case "medicao":
      return "medicao";
    case "investimento":
      return "investimento";
    case "vinculo":
      return "vinculo";
    default:
      return "processo";
  }
}

function asString(value: unknown): string | undefined {
  if (typeof value === "string" && value.trim()) return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return undefined;
}

function detailFromPayload(
  entityType: string,
  action: string,
  payload: Record<string, unknown> | null | undefined
): string | undefined {
  if (!payload) return undefined;

  if (typeof payload.nodes === "number") {
    const unit = action.startsWith("diagram") ? "elemento(s) no diagrama" : "nó(s) no mapeamento";
    return `${payload.nodes} ${unit}`;
  }
  if (typeof payload.overrides === "number") {
    return `${payload.overrides} alteração(ões) no overlay`;
  }
  if (typeof payload.node_notes === "number") {
    return `${payload.node_notes} nota(s) de contexto`;
  }
  if (action === "decomposition.scope.updated" && typeof payload.inherit_all === "boolean") {
    return payload.inherit_all ? "Escopo: herda árvore completa" : "Escopo: nós selecionados";
  }

  const nome = asString(payload.nome_processo);
  const versao = asString(payload.versao_revisao);
  const descricao = asString(payload.descricao_item) ?? asString(payload.descricao_revisao);
  const status = asString(payload.status_processo) ?? asString(payload.status_instancia);
  const rotulo = asString(payload.rotulo_instancia);
  const copiados = payload.copiados;
  const origemProcesso = asString(payload.origem_processo_id);
  const origemInstancia = asString(payload.origem_instancia_id);

  if (action === "duplicate") {
    if (entityType === "processo" && origemProcesso) {
      const extra =
        copiados && typeof copiados === "object"
          ? Object.entries(copiados as Record<string, unknown>)
              .map(([key, value]) => `${key}: ${value}`)
              .join(" · ")
          : undefined;
      return extra ? `Origem ${origemProcesso.slice(0, 8)}… · ${extra}` : `Origem ${origemProcesso}`;
    }
    if (entityType === "processo_instancia" && origemInstancia) {
      return `Replicada de ${origemInstancia.slice(0, 8)}…`;
    }
  }

  if (nome) return nome;
  if (versao) return `Versão ${versao}${asString(payload.cenario_tipo) ? ` · ${payload.cenario_tipo}` : ""}`;
  if (descricao) return descricao;
  if (rotulo) return rotulo;
  if (status) return `Status: ${status}`;

  const keys = Object.keys(payload).filter((key) => !key.endsWith("_id"));
  if (keys.length === 0) return undefined;
  if (keys.length <= 3) {
    return keys
      .map((key) => {
        const value = payload[key];
        if (value == null || value === "") return null;
        return `${key}: ${String(value)}`;
      })
      .filter(Boolean)
      .join(" · ");
  }
  return `${keys.length} campos alterados`;
}

export function formatActorDisplay(
  entry: Pick<ProcessoAuditLogEntry, "user_id" | "user_email" | "user_name">
): string | undefined {
  const name = entry.user_name?.trim();
  const email = entry.user_email?.trim();
  const userId = entry.user_id?.trim();

  if (name && email) return `Por ${name} (${email})`;
  if (name) return `Por ${name}`;
  if (email) return `Por ${email}`;
  if (userId) return `Por ${userId}`;
  return undefined;
}

export function buildProcessoTimeline(entries: ProcessoAuditLogEntry[]): ProcessoTimelineEntry[] {
  return entries
    .map((entry) => {
      const category = categoryForEntityType(entry.entity_type);
      const entityLabel = ENTITY_LABELS[entry.entity_type] ?? entry.entity_type;
      const actionLabel = ACTION_LABELS[entry.action] ?? entry.action.replace(/_/g, " ");
      const detail = detailFromPayload(entry.entity_type, entry.action, entry.payload_json ?? undefined);
      const meta = formatActorDisplay(entry);

      return {
        id: entry.audit_id,
        category,
        title: `${entityLabel} — ${actionLabel}`,
        detail,
        meta,
        occurredAt: entry.created_at,
      };
    })
    .sort((left, right) => Date.parse(left.occurredAt) - Date.parse(right.occurredAt));
}

export function filterProcessoTimelineEntries(
  entries: ProcessoTimelineEntry[],
  filter: ProcessoTimelineFilter
): ProcessoTimelineEntry[] {
  if (filter === "all") return entries;
  return entries.filter((entry) => entry.category === filter);
}
