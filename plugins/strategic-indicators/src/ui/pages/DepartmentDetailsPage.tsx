import { useMemo } from "react";
import { DepartmentDetailHero } from "../components/DepartmentDetailHero";
import { IndicatorDetailGrid } from "../components/IndicatorDetailGrid";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { useStrategicIndicatorsDepartmentDetails } from "../../state/hooks/useStrategicIndicatorsDepartmentDetails";

type DepartmentDetailsPageProps = {
  pathname: string;
  getAccessToken?: () => string | undefined;
};

function extractDepartmentId(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  return parts[parts.length - 1] ?? "";
}

export function DepartmentDetailsPage({
  pathname,
  getAccessToken,
}: DepartmentDetailsPageProps) {
  const departmentId = useMemo(() => extractDepartmentId(pathname), [pathname]);

  const { data, loading, refreshing, error, reload } =
    useStrategicIndicatorsDepartmentDetails({
      departmentId,
      getAccessToken,
    });

  if (loading && !data) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Departamento"
          description="Carregando visão detalhada da área."
          badge={<StatusBadge label="Carregando" variant="neutral" />}
        />

        <InfoState
          title="Carregando departamento"
          description="Aguarde enquanto a visão detalhada é carregada."
        />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Departamento não encontrado"
          description="Não foi possível localizar a área solicitada."
          badge={<StatusBadge label="Indisponível" variant="warning" />}
        />

        <InfoState
          title="Área não localizada"
          description={
            error ??
            "Verifique a rota informada ou retorne para a visão de departamentos."
          }
          actionLabel="Tentar novamente"
          onAction={() => void reload()}
        />
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title={`Departamento — ${data.name}`}
        description="Visão detalhada do IDD departamental com indicadores, metas 2026 e descrição estratégica."
        badge={
          <StatusBadge
            label={loading || refreshing ? "Atualizando" : "Drill-down real"}
            variant={loading || refreshing ? "neutral" : "success"}
          />
        }
      />

      {refreshing ? (
        <InfoState
          title="Atualizando departamento"
          description="Os dados exibidos estão sendo atualizados."
        />
      ) : null}

      {error && data ? (
        <InfoState
          title="Falha ao atualizar departamento"
          description={error}
          actionLabel="Tentar novamente"
          onAction={() => void reload()}
        />
      ) : null}

      <DepartmentDetailHero department={data} />

      <SectionBlock
        title="Indicadores que compõem o IDD"
        description="Os cards abaixo mostram os indicadores oficiais da área, com peso interno, meta 2026 e descrição estratégica."
      >
        <IndicatorDetailGrid indicators={data.indicators} />
      </SectionBlock>
    </div>
  );
}