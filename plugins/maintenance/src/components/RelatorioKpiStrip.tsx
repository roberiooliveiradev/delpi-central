import { AlertTriangle, CheckCircle2, CircleAlert, LineChart } from "lucide-react";
import type { ReactNode } from "react";

import { MaintenanceSimpleKpiCard } from "../app/maintenanceUi";
import { DM_HELP } from "../content/helpTooltips";
import type { PreventivaResumo, RevisaoProgramadaResumo } from "../data/api/maintenanceApi";

type StatusFilterValue = "CRÍTICO" | "ATENÇÃO" | "OK";
type RevisaoStatusFilterValue = "CRÍTICO" | "ATENÇÃO" | "OK";

type FilterKpiTone = "danger" | "warning" | "success";

type RelatorioFilterKpiProps = {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  title: string;
  titleHint?: string;
  value: string | number;
  tone: FilterKpiTone;
};

function RelatorioFilterKpi({
  active,
  onClick,
  icon,
  title,
  titleHint,
  value,
  tone,
}: RelatorioFilterKpiProps) {
  return (
    <MaintenanceSimpleKpiCard
      title={title}
      titleHint={titleHint}
      value={String(value)}
      icon={icon}
      iconTone={tone}
      pressed={active}
      onClick={onClick}
      aria-label={`${active ? "Remover filtro" : "Filtrar por"} ${title}`}
    />
  );
}

export type RelatorioKpiStripProps = {
  mode: "preventiva" | "revisoes";
  resumo: PreventivaResumo | RevisaoProgramadaResumo;
  statusFiltro: StatusFilterValue[];
  revisaoStatusFiltro: RevisaoStatusFilterValue[];
  onToggleStatus: (status: StatusFilterValue) => void;
  onToggleRevisaoStatus: (status: RevisaoStatusFilterValue) => void;
  ultimasTotal?: number;
};

export function RelatorioKpiStrip({
  mode,
  resumo,
  statusFiltro,
  revisaoStatusFiltro,
  onToggleStatus,
  onToggleRevisaoStatus,
  ultimasTotal = 0,
}: RelatorioKpiStripProps) {
  if (mode === "revisoes") {
    const revisaoResumo = resumo as RevisaoProgramadaResumo;
    return (
      <>
        <RelatorioFilterKpi
          active={revisaoStatusFiltro.includes("CRÍTICO")}
          onClick={() => onToggleRevisaoStatus("CRÍTICO")}
          icon={<CircleAlert size={20} aria-hidden="true" />}
          tone="danger"
          title="Revisão vencida"
          titleHint={DM_HELP.relatorio.kpiRevisaoVencida}
          value={revisaoResumo.critico}
        />
        <RelatorioFilterKpi
          active={revisaoStatusFiltro.includes("ATENÇÃO")}
          onClick={() => onToggleRevisaoStatus("ATENÇÃO")}
          icon={<AlertTriangle size={20} aria-hidden="true" />}
          tone="warning"
          title="Próxima do prazo"
          titleHint={DM_HELP.relatorio.kpiRevisaoAtencao}
          value={revisaoResumo.atencao}
        />
        <RelatorioFilterKpi
          active={revisaoStatusFiltro.includes("OK")}
          onClick={() => onToggleRevisaoStatus("OK")}
          icon={<CheckCircle2 size={20} aria-hidden="true" />}
          tone="success"
          title="No prazo"
          titleHint={DM_HELP.relatorio.kpiRevisaoOk}
          value={revisaoResumo.ok}
        />
        <MaintenanceSimpleKpiCard
          title="Ferramentas programadas"
          titleHint={DM_HELP.relatorio.kpiFerramentasProgramadas}
          value={String(revisaoResumo.total)}
          icon={<LineChart size={20} aria-hidden="true" />}
        />
      </>
    );
  }

  const preventivaResumo = resumo as PreventivaResumo;
  return (
    <>
      <RelatorioFilterKpi
        active={statusFiltro.includes("CRÍTICO")}
        onClick={() => onToggleStatus("CRÍTICO")}
        icon={<CircleAlert size={20} aria-hidden="true" />}
        tone="danger"
        title="Crítico"
        titleHint={DM_HELP.relatorio.kpiCritico}
        value={preventivaResumo.critico}
      />
      <RelatorioFilterKpi
        active={statusFiltro.includes("ATENÇÃO")}
        onClick={() => onToggleStatus("ATENÇÃO")}
        icon={<AlertTriangle size={20} aria-hidden="true" />}
        tone="warning"
        title="Atenção"
        titleHint={DM_HELP.relatorio.kpiAtencao}
        value={preventivaResumo.atencao}
      />
      <RelatorioFilterKpi
        active={statusFiltro.includes("OK")}
        onClick={() => onToggleStatus("OK")}
        icon={<CheckCircle2 size={20} aria-hidden="true" />}
        tone="success"
        title="OK"
        titleHint={DM_HELP.relatorio.kpiOk}
        value={preventivaResumo.ok}
      />
      <MaintenanceSimpleKpiCard
        title="Pares monitorados"
        titleHint={DM_HELP.relatorio.kpiParesMonitorados}
        value={String(preventivaResumo.total)}
        subtitle={`${ultimasTotal} últimas reposições na filial`}
        icon={<LineChart size={20} aria-hidden="true" />}
      />
    </>
  );
}
