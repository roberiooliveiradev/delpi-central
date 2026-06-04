import type { AdminQualityUnifiedSummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { formatMetricNumber, formatMetricPercent } from "./adminMetricsFormatters";

type AdminQualityUnifiedMetricsProps = {
  summary: AdminQualityUnifiedSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminQualityUnifiedMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminQualityUnifiedMetricsProps) {
  const health = summary?.health;
  const adoption = summary?.adoption;
  const efficiency = summary?.efficiency;
  const security = summary?.security;

  return (
    <AdminMetricSection
      id="mdc-admin-quality-unified-title"
      domain="Qualidade"
      title="Visão unificada"
      description={`Feedback, adoção, eficiência e segurança consolidados na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando visão unificada..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <AdminKpiGrid>
          <AdminKpiCard title="CSAT" value={formatMetricPercent(health?.csat)} />
          <AdminKpiCard title="Usuários ativos" value={formatMetricNumber(adoption?.activeUsers)} />
          <AdminKpiCard
            title="Mensagens / sessão"
            value={formatMetricNumber(efficiency?.messagesPerSession)}
          />
          <AdminKpiCard
            title="Latência média"
            value={
              efficiency?.latencyAvgMs != null
                ? `${formatMetricNumber(efficiency.latencyAvgMs)} ms`
                : "—"
            }
          />
          <AdminKpiCard title="CTR chips" value={formatMetricPercent(adoption?.chipClickRate)} />
          <AdminKpiCard title="Bloqueios segurança" value={formatMetricNumber(security?.blockedCount)} />
        </AdminKpiGrid>
      ) : null}
    </AdminMetricSection>
  );
}
