import { DepartmentOverviewTable } from "../components/DepartmentOverviewTable";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { useStrategicIndicatorsDepartments } from "../../state/hooks/useStrategicIndicatorsDepartments";

type DepartmentsPageProps = {
  getAccessToken?: () => string | undefined;
};

export function DepartmentsPage({ getAccessToken }: DepartmentsPageProps) {
  const { items, loading, error, reload } = useStrategicIndicatorsDepartments({
    getAccessToken,
  });

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Departamentos"
        description="Visão comparativa inicial dos departamentos que compõem o IGD, com peso oficial, nota resumida e acesso ao drill-down por área."
        badge={
          <StatusBadge
            label={loading ? "Carregando" : "API Real"}
            variant={loading ? "neutral" : "success"}
          />
        }
      />

      <SectionBlock
        title="Comparativo departamental"
        description="Cada linha representa um departamento oficial do IGD, com acesso à visão específica do seu IDD."
      >
        {loading ? (
          <InfoState
            title="Carregando departamentos"
            description="Aguarde enquanto a visão comparativa é carregada."
          />
        ) : error ? (
          <InfoState
            title="Falha ao carregar departamentos"
            description={error}
            actionLabel="Tentar novamente"
            onAction={() => void reload()}
          />
        ) : (
          <DepartmentOverviewTable departments={items} />
        )}
      </SectionBlock>
    </div>
  );
}