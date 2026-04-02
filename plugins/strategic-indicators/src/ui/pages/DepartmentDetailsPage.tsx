import { useMemo } from "react";
import { getDepartmentById } from "../../data/mocks/departmentsMock";
import { DepartmentDetailHero } from "../components/DepartmentDetailHero";
import { IndicatorDetailGrid } from "../components/IndicatorDetailGrid";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";

type DepartmentDetailsPageProps = {
  pathname: string;
};

function extractDepartmentId(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  return parts[parts.length - 1] ?? "";
}

export function DepartmentDetailsPage({
  pathname,
}: DepartmentDetailsPageProps) {
  const departmentId = useMemo(() => extractDepartmentId(pathname), [pathname]);
  const department = useMemo(() => getDepartmentById(departmentId), [departmentId]);

  if (!department) {
    return (
      <div className="si-page">
        <PageHeader
          eyebrow="MinhaDelpi"
          title="Departamento não encontrado"
          description="Não foi possível localizar a área solicitada neste MVP."
          badge={<StatusBadge label="Indisponível" variant="warning" />}
        />

        <InfoState
          title="Área não localizada"
          description="Verifique a rota informada ou retorne para a visão de departamentos."
        />
      </div>
    );
  }

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title={`Departamento — ${department.name}`}
        description="Visão inicial do IDD departamental com indicadores, metas 2026 e descrição estratégica."
        badge={<StatusBadge label="Drill-down inicial" variant="info" />}
      />

      <DepartmentDetailHero department={department} />

      <SectionBlock
        title="Indicadores que compõem o IDD"
        description="Os cards abaixo mostram os indicadores oficiais da área, com peso interno, meta 2026 e descrição estratégica."
      >
        <IndicatorDetailGrid indicators={department.indicators} />
      </SectionBlock>
    </div>
  );
}