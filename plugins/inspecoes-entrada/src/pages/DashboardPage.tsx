import { useEffect } from "react";

import { DashboardSection } from "../components/DashboardSection";
import { PendingInspectionsTable } from "../components/PendingInspectionsTable";
import { RejectedProductsList } from "../components/RejectedProductsList";
import { SummaryCards } from "../components/SummaryCards";
import { SupplierPendingList } from "../components/SupplierPendingList";
import { useInspecoesEntradaDashboard } from "../hooks/useInspecoesEntradaDashboard";

type DashboardPageProps = {
  branch: string;
  refreshToken: number;
  onLoadingChange?: (loading: boolean) => void;
  onLastUpdated?: (date: Date) => void;
};

export function DashboardPage({
  branch,
  refreshToken,
  onLoadingChange,
  onLastUpdated,
}: DashboardPageProps) {
  const { resumo, pendentes, fornecedores, rejeitadas, loading } =
    useInspecoesEntradaDashboard(branch, refreshToken);

  useEffect(() => {
    onLoadingChange?.(loading);
  }, [onLoadingChange, loading]);

  useEffect(() => {
    if (!loading && resumo.data) {
      onLastUpdated?.(new Date());
    }
  }, [loading, resumo.data, refreshToken, onLastUpdated]);

  return (
    <div className="ie-dashboard-layout">
      <SummaryCards resumo={resumo.data} loading={resumo.loading} error={resumo.error} />

      <div className="ie-dashboard-grid ie-dashboard-grid--analytics">
        <DashboardSection
          title="Gargalos por fornecedor"
          subtitle="Fornecedores com materiais aguardando inspeção"
          variant="analytics"
        >
          <SupplierPendingList
            items={fornecedores.data?.items ?? []}
            loading={fornecedores.loading}
            error={fornecedores.error}
            totalPending={fornecedores.data?.total_pending}
          />
        </DashboardSection>

        <DashboardSection
          title="Produtos rejeitados"
          subtitle="Inspeções reprovadas com produto, fornecedor e data do laudo"
          variant="analytics"
        >
          <RejectedProductsList
            items={rejeitadas.data?.items ?? []}
            loading={rejeitadas.loading}
            error={rejeitadas.error}
            total={rejeitadas.data?.total}
          />
        </DashboardSection>
      </div>

      <DashboardSection
        title="Pendências"
        subtitle="Materiais aguardando inspeção de recebimento"
        variant="preview"
        action={
          pendentes.data ? (
            <span className="ie-section-total">
              {pendentes.data.pagination.total.toLocaleString("pt-BR")} pend.
            </span>
          ) : undefined
        }
      >
        <PendingInspectionsTable
          items={pendentes.data?.items ?? []}
          loading={pendentes.loading}
          error={pendentes.error}
          totalCount={pendentes.data?.pagination.total}
        />
      </DashboardSection>
    </div>
  );
}
