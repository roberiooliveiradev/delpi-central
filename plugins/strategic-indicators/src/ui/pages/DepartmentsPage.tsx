import { useMemo, useState } from "react";
import { DepartmentOverviewTable } from "../components/DepartmentOverviewTable";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { useStrategicIndicatorsDepartments } from "../../state/hooks/useStrategicIndicatorsDepartments";

type DepartmentsPageProps = {
  getAccessToken?: () => string | undefined;
};

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

export function DepartmentsPage({ getAccessToken }: DepartmentsPageProps) {
  const [referenceMonth, setReferenceMonth] = useState(getCurrentMonthValue());

  const { startDate, endDate } = useMemo(
    () => buildMonthRange(referenceMonth),
    [referenceMonth],
  );

  const { items, loading, refreshing, error, reload } =
    useStrategicIndicatorsDepartments({
      competence: referenceMonth,
      startDate,
      endDate,
      getAccessToken,
    });

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Departamentos"
        description="Visão comparativa dos departamentos que compõem o IGD, com peso oficial, nota resumida e acesso ao drill-down por área."
        badge={
          <StatusBadge
            label={loading || refreshing ? "Atualizando" : "API Real"}
            variant={loading || refreshing ? "neutral" : "success"}
          />
        }
      />

      <SectionBlock
        title="Filtro de referência"
        description="Selecione o mês de referência para consultar a composição departamental do período."
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

      <SectionBlock
        title="Comparativo departamental"
        description="Cada linha representa um departamento oficial do IGD, com acesso à visão específica do seu IDD."
      >
        {loading && items.length === 0 ? (
          <InfoState
            title="Carregando departamentos"
            description="Aguarde enquanto a visão comparativa é carregada."
          />
        ) : error && items.length === 0 ? (
          <InfoState
            title="Falha ao carregar departamentos"
            description={error}
            actionLabel="Tentar novamente"
            onAction={() => void reload()}
          />
        ) : (
          <>
            {refreshing ? (
              <InfoState
                title="Atualizando departamentos"
                description="Os dados exibidos estão sendo atualizados para o novo período."
              />
            ) : null}

            {error && items.length > 0 ? (
              <InfoState
                title="Falha ao atualizar departamentos"
                description={error}
                actionLabel="Tentar novamente"
                onAction={() => void reload()}
              />
            ) : null}

            <DepartmentOverviewTable departments={items} />
          </>
        )}
      </SectionBlock>
    </div>
  );
}