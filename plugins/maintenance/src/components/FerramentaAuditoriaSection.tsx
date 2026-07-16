import { useCallback, useEffect, useMemo, useState } from "react";
import { CircleAlert, FilePenLine, PlusCircle, Trash2 } from "lucide-react";
import {
  createDashboardSectionCard,
  sectionCardPacBemClasses,
  type TimelineItemModel,
  type TimelineTone,
} from "@delpi/plugin-ui/index";

import { auditActionLabel, auditPayloadSummary, formatAuditUser } from "../content/auditLabels";
import { fetchFerramentaAuditoria, type FerramentaAuditItem } from "../data/api/maintenanceApi";
import { useServerTable } from "../hooks/useServerTable";
import { Pagination, Timeline } from "./data";

type FerramentaAuditoriaSectionProps = {
  filial: string;
  codigoFerramenta: string;
  reloadKey?: number;
  getAccessToken?: () => string | undefined;
};

const SectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses("dm"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function auditActionTone(acao: string): TimelineTone {
  if (acao.endsWith(".delete")) return "danger";
  if (acao.endsWith(".update")) return "warning";
  if (acao.endsWith(".create") || acao.endsWith(".registrar")) return "success";
  return "info";
}

function auditActionMarker(acao: string) {
  if (acao.endsWith(".delete")) return <Trash2 size={12} strokeWidth={2.25} />;
  if (acao.endsWith(".update")) return <FilePenLine size={12} strokeWidth={2.25} />;
  if (acao.endsWith(".create") || acao.endsWith(".registrar")) {
    return <PlusCircle size={12} strokeWidth={2.25} />;
  }
  return <CircleAlert size={12} strokeWidth={2.25} />;
}

function toTimelineItem(item: FerramentaAuditItem): TimelineItemModel {
  const userLabel = formatAuditUser(item.usuario_nome, item.usuario_sub);
  const userId = item.usuario_sub?.trim();

  return {
    id: item.audit_id,
    title: auditActionLabel(item.acao),
    occurredAt: item.data_criacao,
    timeLabel: formatDateTime(item.data_criacao),
    detail: auditPayloadSummary(item.payload),
    meta:
      item.usuario_nome?.trim() && userId ? (
        <span title={userId}>Usuário: {userLabel}</span>
      ) : (
        `Usuário: ${userLabel}`
      ),
    tone: auditActionTone(item.acao),
    marker: auditActionMarker(item.acao),
  };
}

export function FerramentaAuditoriaSection({
  filial,
  codigoFerramenta,
  reloadKey = 0,
  getAccessToken,
}: FerramentaAuditoriaSectionProps) {
  const auditTable = useServerTable({ pageSize: 10 });
  const [items, setItems] = useState<FerramentaAuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAuditoria = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFerramentaAuditoria(
        {
          filial,
          codigoFerramenta,
          page: auditTable.query.page,
          pageSize: auditTable.query.pageSize,
        },
        getAccessToken,
      );
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar auditoria.");
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [
    auditTable.query.page,
    auditTable.query.pageSize,
    codigoFerramenta,
    filial,
    getAccessToken,
  ]);

  useEffect(() => {
    void loadAuditoria();
  }, [loadAuditoria, reloadKey]);

  const timelineItems = useMemo(() => items.map(toTimelineItem), [items]);

  return (
    <>
      {error ? <p className="dm-inline-error">{error}</p> : null}
      <SectionCard
        title="Auditoria da ferramenta"
        hint="Registro cronológico de reposições e revisões programadas desta ferramenta."
        subtitle="Eventos em ordem do mais recente para o mais antigo."
        actions={<span className="dm-badge">{total} evento(s)</span>}
      >
        <Timeline
          items={timelineItems}
          loading={loading}
          emptyMessage="Nenhum evento registrado para esta ferramenta."
          aria-label="Auditoria da ferramenta"
        />
        <div className="dm-auditoria-timeline__footer">
          <Pagination
            page={auditTable.query.page}
            pageSize={auditTable.query.pageSize}
            total={total}
            onPageChange={auditTable.setPage}
            hideWhenSinglePage
          />
        </div>
      </SectionCard>
    </>
  );
}
