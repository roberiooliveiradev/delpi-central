import { departmentsMock } from "../../data/mocks/departmentsMock";
import { DepartmentOverviewTable } from "../components/DepartmentOverviewTable";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";

export function DepartmentsPage() {
  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Departamentos"
        description="Visão comparativa inicial dos departamentos que compõem o IGD, com peso oficial, nota resumida e acesso ao drill-down por área."
        badge={<StatusBadge label="MVP Analítico" variant="info" />}
      />

      <SectionBlock
        title="Comparativo departamental"
        description="Cada linha representa um departamento oficial do IGD, com acesso à visão específica do seu IDD."
      >
        <DepartmentOverviewTable departments={departmentsMock} />
      </SectionBlock>
    </div>
  );
}