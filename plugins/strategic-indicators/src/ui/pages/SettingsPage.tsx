import { useMemo, useState } from "react";
import { PageHeader } from "../components/PageHeader";
import { SettingsHero } from "../components/SettingsHero";
import { SettingsStatusStrip } from "../components/SettingsStatusStrip";
import { SettingsParametersPanel } from "../components/SettingsParametersPanel";
import { SettingsGovernancePanel } from "../components/SettingsGovernancePanel";
import { AuditWorkspacePanel } from "../components/AuditWorkspacePanel";
import { SectionBlock } from "../components/SectionBlock";
import { InfoState } from "../components/InfoState";
import { SettingsSummaryCards } from "../components/SettingsSummaryCards";
import { useStrategicIndicatorsSettings } from "../../state/hooks/useStrategicIndicatorsSettings";
import { AdminDepartmentsWorkspace } from "../components/AdminDepartmentsWorkspace";
import { AnnualGoalsWorkspace } from "../components/AnnualGoalsWorkspace";
import type { SettingsDashboardData } from "../../data/types/settingsDashboard";

type SettingsPageProps = {
  getAccessToken?: () => string | undefined;
};

type SettingsTab =
  | "overview"
  | "departments"
  | "goals"
  | "global"
  | "audit";

export function SettingsPage({
  getAccessToken,
}: SettingsPageProps) {
  const settings = useStrategicIndicatorsSettings({ getAccessToken });
  const [activeTab, setActiveTab] = useState<SettingsTab>("overview");

  const dashboardData = useMemo<SettingsDashboardData | null>(() => {
    if (!settings.data) return null;

    return {
      weights: settings.data.weights.items.map((item) => ({
        id: item.department_id,
        departmentName: item.department_name,
        weightPct: item.weight_pct,
        note: `Peso executivo atual do departamento ${item.department_name}.`,
      })),
      goals: settings.data.goals.items.map((item) => ({
        id: item.department_id,
        departmentName: item.department_name,
        headlineGoal: item.headline_goal,
        supportingFocus: item.supporting_focus,
      })),
      parameters: settings.data.parameters.items.map((item, index) => ({
        id: `${item.key}-${index}`,
        label: item.label,
        value: item.value,
        observation: item.key,
      })),
      governance: settings.data.governance.items.map((item, index) => ({
        id: `${item.key}-${index}`,
        label: item.label,
        value: item.value,
        observation: item.observation,
      })),
      readiness: [],
      meta: {
        source: settings.data.meta.source,
        updatedAt: settings.data.meta.updated_at,
        updatedByEmail: settings.data.meta.updated_by_email,
      },
    };
  }, [settings.data]);

  return (
    <div className="si-settings-page">
      <PageHeader
        eyebrow="Strategic Indicators"
        title="Administração do módulo"
        description="Central de gestão para estrutura organizacional, catálogo de indicadores, metas anuais, parâmetros globais e trilha de auditoria."
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
            className={`si-settings-tabbar__item ${activeTab === tabId ? "is-active" : ""}`}
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
            description="Resumo executivo do estado atual da administração do módulo."
          >
            {!dashboardData ? (
              <InfoState
                title="Carregando painel administrativo"
                description="Aguarde enquanto o overview do módulo é carregado."
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
                      Origem do overview
                    </span>
                    <strong className="si-settings-overview-card__value">
                      {dashboardData.meta.source}
                    </strong>
                    <p>
                      Fonte declarada pelo backend para composição das configurações exibidas.
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
            description="Gerencie a estrutura administrativa do módulo e o catálogo estrutural de cada área."
          >
            <AdminDepartmentsWorkspace getAccessToken={getAccessToken} />
          </SectionBlock>
        ) : null}

        {activeTab === "goals" ? (
          <SectionBlock
            title="Metas anuais"
            description="Organize ciclos anuais, monitore a cobertura das metas e execute ações administrativas em lote."
          >
            <AnnualGoalsWorkspace getAccessToken={getAccessToken} />
          </SectionBlock>
        ) : null}

        {activeTab === "global" ? (
          <SectionBlock
            title="Configurações globais"
            description="Administre os blocos globais que continuam centralizados no módulo."
          >
            {!settings.data ? (
              <InfoState
                title="Carregando configurações globais"
                description="Aguarde enquanto parâmetros e governança são carregados."
              />
            ) : (
              <div className="si-settings-global-grid">
                <SettingsParametersPanel
                  items={dashboardData?.parameters ?? []}
                />
                <SettingsGovernancePanel
                  items={dashboardData?.governance ?? []}
                />
              </div>
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