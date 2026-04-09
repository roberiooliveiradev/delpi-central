import { useMemo, useState } from "react";
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

function getCurrentMonthValue() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function buildMonthRange(monthValue: string) {
  if (!monthValue) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const [yearStr, monthStr] = monthValue.split("-");
  const year = Number(yearStr);
  const month = Number(monthStr);

  if (!year || !month) {
    return {
      startDate: undefined,
      endDate: undefined,
    };
  }

  const firstDay = `01-${String(month).padStart(2, "0")}-${year}`;
  const lastDayDate = new Date(year, month, 0);
  const lastDay = `${String(lastDayDate.getDate()).padStart(2, "0")}-${String(
    month,
  ).padStart(2, "0")}-${year}`;

  return {
    startDate: firstDay,
    endDate: lastDay,
  };
}

export function DepartmentDetailsPage({
  pathname,
  getAccessToken,
}: DepartmentDetailsPageProps) {
  const departmentId = useMemo(() => extractDepartmentId(pathname), [pathname]);
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());

  const { startDate, endDate } = useMemo(
    () => buildMonthRange(referenceMonth),
    [referenceMonth],
  );

  const { data, loading, refreshing, error, reload } =
    useStrategicIndicatorsDepartmentDetails({
      departmentId,
      competence: referenceMonth,
      startDate,
      endDate,
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

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência para consultar o detalhe do departamento."
        >
          <div className="si-form-grid">
            <label className="si-field">
              <span className="si-field__label">Mês de referência</span>
              <input
                type="month"
                className="si-input"
                value={referenceMonth}
                onChange={(event) => setReferenceMonth(event.target.value)}
              />
            </label>
          </div>
        </SectionBlock>

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

        <SectionBlock
          title="Filtro de referência"
          description="Selecione o mês de referência para consultar o detalhe do departamento."
        >
          <div className="si-form-grid">
            <label className="si-field">
              <span className="si-field__label">Mês de referência</span>
              <input
                type="month"
                className="si-input"
                value={referenceMonth}
                onChange={(event) => setReferenceMonth(event.target.value)}
              />
            </label>
          </div>
        </SectionBlock>

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
        description={`Visão detalhada do IDD departamental no período ${referenceMonth}.`}
        badge={
          <StatusBadge
            label={loading || refreshing ? "Atualizando" : "Drill-down real"}
            variant={loading || refreshing ? "neutral" : "success"}
          />
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência para consultar o detalhe do departamento."
      >
        <div className="si-form-grid">
          <label className="si-field">
            <span className="si-field__label">Mês de referência</span>
            <input
              type="month"
              className="si-input"
              value={referenceMonth}
              onChange={(event) => setReferenceMonth(event.target.value)}
            />
          </label>
        </div>
      </SectionBlock>

      {refreshing ? (
        <InfoState
          title="Atualizando departamento"
          description="Os dados exibidos estão sendo atualizados para o novo período."
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
        description="Os cards abaixo mostram os indicadores oficiais da área, com peso interno, meta estruturada e descrição estratégica."
      >
        <IndicatorDetailGrid indicators={data.indicators} />
      </SectionBlock>
    </div>
  );
}