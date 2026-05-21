import { useMemo, useState } from "react";
import { PageHeader } from "../components/PageHeader";
import { SettingsHero } from "../components/SettingsHero";
import { SettingsStatusStrip } from "../components/SettingsStatusStrip";
import { AuditWorkspacePanel } from "../components/AuditWorkspacePanel";
import { SectionBlock } from "../components/SectionBlock";
import { InfoState } from "../components/InfoState";
import { SettingsSummaryCards } from "../components/SettingsSummaryCards";
import { useStrategicIndicatorsSettings } from "../../state/hooks/useStrategicIndicatorsSettings";
import type { SettingsDashboardData } from "../../data/types/settingsDashboard";
import type {
  SettingsWeightItem,
  SettingsGoalItem,
  SettingsParameterItem,
  SettingsGovernanceItem,
} from "../../data/types/settings";

import { AdminDepartmentsWorkspace } from "../components/AdminDepartmentsWorkspace";
import { AdminGoalsWorkspace } from "../components/AdminGoalsWorkspace";
import { SettingsStructuredEditor } from "../components/SettingsStructuredEditor";
import {
  getMetaSourceLabel,
} from "../presentation/labels";
import "./SettingsPage.css";


type SettingsPageProps = {
  getAccessToken?: () => string | undefined;
};

type SettingsTab =
  | "overview"
  | "departments"
  | "goals"
  | "global"
  | "audit";

export function SettingsPage({ getAccessToken }: SettingsPageProps) {
  const settings = useStrategicIndicatorsSettings({ getAccessToken });
  const [activeTab, setActiveTab] = useState<SettingsTab>("overview");

  const dashboardData = useMemo<SettingsDashboardData | null>(() => {
    if (!settings.data) return null;

    return {
      weights: settings.data.weights.items.map((item: SettingsWeightItem) => ({
        id: item.department_id,
        departmentName: item.department_name,
        weightPct: item.weight_pct,
        note: "Bloco legado do painel. A edição principal agora ocorre via departamentos.",
      })),

      goals: settings.data.goals.items.map((item: SettingsGoalItem) => ({
        id: item.department_id,
        departmentName: item.department_name,
        headlineGoal: item.headline_goal,
        supportingFocus: item.supporting_focus,
      })),

      parameters: settings.data.parameters.items.map(
        (item: SettingsParameterItem, index: number) => ({
          id: `${item.key}-${index}`,
          label: item.label,
          value: item.value,
          observation: item.key,
        }),
      ),

      governance: settings.data.governance.items.map(
        (item: SettingsGovernanceItem, index: number) => ({
          id: `${item.key}-${index}`,
          label: item.label,
          value: item.value,
          observation: item.observation,
        }),
      ),
      readiness: [
        {
          id: "departments-admin",
          title: "Administração de departamentos",
          status: "ready",
          description:
            "Fluxo principal do catálogo estrutural do módulo.",
        },
        {
          id: "annual-goals-admin",
          title: "Metas anuais",
          status: "ready",
          description:
            "Fluxo principal para metas analíticas, ciclos anuais e operações em lote.",
        },
        {
          id: "global-settings",
          title: "Configurações globais",
          status: "ready",
          description:
            "Escopo reduzido a parâmetros e governança.",
        },
      ],
      meta: {
        source: getMetaSourceLabel(settings.data.meta.source),
        updatedAt: settings.data.meta.updated_at,
        updatedByEmail: settings.data.meta.updated_by_email,
      },
    };
  }, [settings.data]);

  return (
    <div className="si-settings-page">
      <PageHeader
        eyebrow="Indicadores Estratégicos"
        title="Administração do módulo"
        description="Central administrativa do modelo novo: departamentos, indicadores estruturais, metas anuais, parâmetros globais e auditoria."
      />

      <SettingsHero
        routePath="/apps/strategic-indicators/settings"
        permissionCode="strategic-indicators.settings.manage"
      />

      <SettingsStatusStrip
        loading={settings.loading}
        error={settings.error}
        successMessage={settings.successMessage}
        updatedAt={settings.data?.meta.updated_at ?? null}
        updatedByEmail={settings.data?.meta.updated_by_email ?? null}
        onRetry={() => void settings.reload()}
        onDismissSuccess={settings.clearSuccessMessage}
      />

      <div className="si-settings-tabbar">
        {([
          ["overview", "Painel"],
          ["departments", "Departamentos"],
          ["goals", "Metas anuais"],
          ["global", "Configurações globais"],
          ["audit", "Auditoria"],
        ] as const).map(([tabId, label]) => (
          <button
            key={tabId}
            type="button"
            className={`si-settings-tabbar__item ${
              activeTab === tabId ? "is-active" : ""
            }`}
            onClick={() => setActiveTab(tabId)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="si-settings-sections">
        {activeTab === "overview" ? (
          <SectionBlock
            title="Painel administrativo"
            description="Resumo executivo do estado atual do módulo. Os blocos de pesos e metas abaixo são visão de leitura, não a base principal de edição."
          >
            {!dashboardData ? (
              <InfoState
                title="Carregando painel administrativo"
                description="Aguarde enquanto o painel do módulo é carregado."
              />
            ) : (
              <>
                <SettingsSummaryCards data={dashboardData} />

                <div className="si-settings-overview-grid">
                  <article className="si-settings-overview-card">
                    <span className="si-settings-overview-card__label">
                      Última atualização
                    </span>
                    <strong className="si-settings-overview-card__value">
                      {dashboardData.meta.updatedAt
                        ? new Date(dashboardData.meta.updatedAt).toLocaleDateString("pt-BR")
                        : "—"}
                    </strong>
                    <p>
                      {dashboardData.meta.updatedByEmail
                        ? `Registro mais recente por ${dashboardData.meta.updatedByEmail}.`
                        : "Sem identificação de autor no registro atual."}
                    </p>
                  </article>

                  <article className="si-settings-overview-card">
                    <span className="si-settings-overview-card__label">
                      Fonte declarada
                    </span>
                    <strong className="si-settings-overview-card__value">
                      {dashboardData.meta.source}
                    </strong>
                    <p>
                      O backend ainda pode retornar blocos legados para o painel, mas a escrita principal permanece no modelo novo.
                    </p>
                  </article>

                  <article className="si-settings-overview-card">
                    <span className="si-settings-overview-card__label">
                      Centro da administração
                    </span>
                    <strong className="si-settings-overview-card__value">
                      Departamentos e metas anuais
                    </strong>
                    <p>
                      Use as abas dedicadas para editar catálogo estrutural e ciclos anuais. Configurações globais ficaram restritas a parâmetros e governança.
                    </p>
                  </article>
                </div>
              </>
            )}
          </SectionBlock>
        ) : null}

        {activeTab === "departments" ? (
          <SectionBlock
            title="Departamentos"
            description="Gerencie a estrutura administrativa do módulo e abra cada departamento em um workspace focado no catálogo estrutural."
          >
            <AdminDepartmentsWorkspace getAccessToken={getAccessToken} />
          </SectionBlock>
        ) : null}

        {activeTab === "goals" ? (
          <SectionBlock
            title="Metas anuais"
            description="Gerencie ciclos anuais, metas por indicador e operações em lote como duplicação e preenchimento."
          >
            <AdminGoalsWorkspace getAccessToken={getAccessToken} />
          </SectionBlock>
        ) : null}

        {activeTab === "global" ? (
          <SectionBlock
            title="Configurações globais"
            description="Administre apenas os blocos globais centrais do módulo: parâmetros e governança."
          >
            {!settings.data ? (
              <InfoState
                title="Carregando configurações globais"
                description="Aguarde enquanto parâmetros e governança são carregados."
              />
            ) : (
              <SettingsStructuredEditor
                data={settings.data}
                saving={settings.saving}
                onSave={settings.save}
              />
            )}
          </SectionBlock>
        ) : null}

        {activeTab === "audit" ? (
          <SectionBlock
            title="Auditoria"
            description="Acompanhe as mudanças administrativas recentes e filtre a trilha por bloco funcional."
          >
            <AuditWorkspacePanel getAccessToken={getAccessToken} />
          </SectionBlock>
        ) : null}
      </div>
    </div>
  );
}