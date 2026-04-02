import { alertsMock } from "../../data/mocks/alertsMock";
import { AlertsExecutiveAction } from "../components/AlertsExecutiveAction";
import { AlertsPriorityHighlights } from "../components/AlertsPriorityHighlights";
import { AlertsSummaryCards } from "../components/AlertsSummaryCards";
import { CriticalDepartmentList } from "../components/CriticalDepartmentList";
import { CriticalIndicatorList } from "../components/CriticalIndicatorList";
import { ExecutiveAlertsList } from "../components/ExecutiveAlertsList";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";
import { TopAlertHighlight } from "../components/TopAlertHighlight";

export function AlertsPage() {
  const data = alertsMock;
  const topExecutiveAlert = data.executiveAlerts[0] ?? null;

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Alertas"
        description="Visão inicial de criticidade e priorização do painel, destacando o que exige ação executiva e operacional."
        badge={<StatusBadge label="MVP Acionável" variant="warning" />}
      />

      <SectionBlock
        title="Síntese de criticidade"
        description="Resumo da condição atual do índice e da distribuição dos alertas do painel."
      >
        <AlertsSummaryCards data={data} />
      </SectionBlock>

      <SectionBlock
        title="Direcionamento executivo"
        description="Leitura objetiva do que deve ser atacado primeiro no cenário atual."
      >
        <div className="si-alerts-executive-layout">
          <AlertsExecutiveAction data={data} />
          <TopAlertHighlight alert={topExecutiveAlert} />
        </div>
      </SectionBlock>

      <SectionBlock
        title="Destaques de priorização"
        description="Recorte direto da área e do indicador que mais exigem ação no cenário atual."
      >
        <AlertsPriorityHighlights data={data} />
      </SectionBlock>

      <SectionBlock
        title="Alertas executivos"
        description="Leitura resumida dos principais sinais executivos do painel."
      >
        <ExecutiveAlertsList alerts={data.executiveAlerts} />
      </SectionBlock>

      <SectionBlock
        title="Departamentos prioritários"
        description="Áreas que exigem acompanhamento mais próximo no cenário atual."
      >
        <CriticalDepartmentList alerts={data.departmentAlerts} />
      </SectionBlock>

      <SectionBlock
        title="Indicadores prioritários"
        description="Indicadores com maior necessidade de atenção no recorte analítico atual."
      >
        <CriticalIndicatorList alerts={data.indicatorAlerts} />
      </SectionBlock>
    </div>
  );
}