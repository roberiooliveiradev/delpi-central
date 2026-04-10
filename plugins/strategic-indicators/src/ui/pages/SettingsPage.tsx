import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { SettingsActionPanel } from "../components/SettingsActionPanel";
import { SettingsStructuredEditor } from "../components/SettingsStructuredEditor";
import { SettingsExecutiveHighlight } from "../components/SettingsExecutiveHighlight";
import { SettingsGoalsPanel } from "../components/SettingsGoalsPanel";
import { SettingsGovernancePanel } from "../components/SettingsGovernancePanel";
import { SettingsHero } from "../components/SettingsHero";
import { SettingsParametersPanel } from "../components/SettingsParametersPanel";
import { SettingsReadinessPanel } from "../components/SettingsReadinessPanel";
import { SettingsSummaryCards } from "../components/SettingsSummaryCards";
import { SettingsWeightsPanel } from "../components/SettingsWeightsPanel";
import { StatusBadge } from "../components/StatusBadge";
import { AuditWorkspacePanel } from "../components/AuditWorkspacePanel";
import { SettingsWorkspaceNav } from "../components/SettingsWorkspaceNav";
import { SettingsStatusStrip } from "../components/SettingsStatusStrip";
import { InfoState } from "../components/InfoState";
import { IndicatorGoalsWorkspace } from "../components/IndicatorGoalsWorkspace";
import { useStrategicIndicatorsSettings } from "../../state/hooks/useStrategicIndicatorsSettings";
import type {
  SettingsDashboardData,
  SettingsReadinessItem,
} from "../../data/types/settingsDashboard";

type SettingsPageProps = {
  getAccessToken?: () => string | undefined;
};

const readinessItems: SettingsReadinessItem[] = [
  {
    id: "readiness-1",
    title: "Leitura real da configuração",
    status: "ready",
    description:
      "A rota /settings já consome dados persistidos via api-delpi.",
  },
  {
    id: "readiness-2",
    title: "Atualização administrativa inicial",
    status: "ready",
    description:
      "O backend já aceita atualização dos quatro blocos principais.",
  },
  {
    id: "readiness-3",
    title: "Permissão fina por ação",
    status: "planned",
    description:
      "Próxima evolução natural para endurecer a governança da edição.",
  },
  {
    id: "readiness-4",
    title: "Auditoria avançada",
    status: "mock",
    description:
      "Ainda não entra nesta fase para manter o escopo disciplinado.",
  },
];

const settingsNavItems = [
  { id: "settings-overview", label: "Visão geral" },
  { id: "settings-parameters", label: "Parâmetros" },
  { id: "settings-weights", label: "Pesos" },
  { id: "settings-goals", label: "Metas" },
  { id: "settings-governance", label: "Governança" },
  { id: "settings-readiness", label: "Prontidão" },
  { id: "settings-next-action", label: "Próxima ação" },
  { id: "settings-editor", label: "Edição" },
  { id: "settings-indicator-goals", label: "Metas analíticas" },
  { id: "settings-audit", label: "Auditoria" },
];

export function SettingsPage({ getAccessToken }: SettingsPageProps) {
  const {
    data,
    loading,
    refreshing,
    saving,
    error,
    successMessage,
    save,
    reload,
    clearSuccessMessage,
  } = useStrategicIndicatorsSettings({ getAccessToken });

  const settingsDashboardData: SettingsDashboardData | null = data
    ? {
        weights: data.weights.items.map((item) => ({
          id: item.department_id,
          departmentName: item.department_name,
          weightPct: item.weight_pct,
          note: "",
        })),
        goals: data.goals.items.map((item) => ({
          id: item.department_id,
          departmentName: item.department_name,
          headlineGoal: item.headline_goal,
          supportingFocus: item.supporting_focus,
        })),
        parameters: data.parameters.items.map((item) => ({
          id: item.key,
          label: item.label,
          value: item.value,
          observation: "",
        })),
        governance: data.governance.items.map((item) => ({
          id: item.key,
          label: item.label,
          value: item.value,
          observation: item.observation,
        })),
        readiness: readinessItems,
      }
    : null;

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Configurações"
        description="Workspace administrativo do módulo, consolidando governança, persistência real, auditoria e preparação para futuras evoluções controladas."
        badge={
          <StatusBadge
            label={loading || refreshing ? "Atualizando" : "Admin Workspace"}
            variant={loading || refreshing ? "neutral" : "success"}
          />
        }
      />

      <SettingsHero
        routePath="/apps/strategic-indicators/settings"
        permissionCode="strategic-indicators.settings.manage"
      />

      <SettingsStatusStrip
        loading={loading}
        error={error}
        successMessage={successMessage}
        updatedAt={data?.meta?.updated_at ?? null}
        updatedByEmail={data?.meta?.updated_by_email ?? null}
        onRetry={() => void reload()}
        onDismissSuccess={clearSuccessMessage}
      />

      {refreshing && data ? (
        <InfoState
          title="Atualizando configurações"
          description="Os dados exibidos estão sendo atualizados sem desmontar a tela."
        />
      ) : null}

      {!loading && data && settingsDashboardData ? (
        <>
          <SettingsWorkspaceNav items={settingsNavItems} />

          <div id="settings-overview">
            <SectionBlock
              title="Destaque administrativo"
              description="Síntese executiva da governança estrutural do módulo."
            >
              <SettingsExecutiveHighlight data={settingsDashboardData} />
            </SectionBlock>

            <SectionBlock
              title="Síntese administrativa"
              description="Resumo rápido do estado de governança do módulo nesta fase."
            >
              <SettingsSummaryCards data={settingsDashboardData} />
            </SectionBlock>
          </div>

          <div id="settings-parameters">
            <SectionBlock
              title="Parâmetros globais"
              description="Elementos estruturais do módulo que definem a leitura oficial do painel."
            >
              <SettingsParametersPanel items={settingsDashboardData.parameters} />
            </SectionBlock>
          </div>

          <div id="settings-weights">
            <SectionBlock
              title="Pesos oficiais"
              description="Composição governada do IGD conforme o documento consolidado."
            >
              <SettingsWeightsPanel items={settingsDashboardData.weights} />
            </SectionBlock>
          </div>

          <div id="settings-goals">
            <SectionBlock
              title="Metas resumidas"
              description="Referências executivas das metas mais importantes por área."
            >
              <SettingsGoalsPanel items={settingsDashboardData.goals} />
            </SectionBlock>
          </div>

          <div id="settings-governance">
            <SectionBlock
              title="Governança do módulo"
              description="Parâmetros administrativos e observações da fase atual do painel."
            >
              <SettingsGovernancePanel items={settingsDashboardData.governance} />
            </SectionBlock>
          </div>

          <div id="settings-readiness">
            <SectionBlock
              title="Prontidão administrativa"
              description="Leitura do que já está pronto e do que ainda evoluirá para persistência real."
            >
              <SettingsReadinessPanel items={readinessItems} />
            </SectionBlock>
          </div>

          <div id="settings-next-action">
            <SectionBlock
              title="Próxima ação"
              description="Resumo do próximo passo administrativo mais natural do módulo."
            >
              <SettingsActionPanel data={settingsDashboardData} />
            </SectionBlock>
          </div>

          <div id="settings-editor">
            <SectionBlock
              title="Edição administrativa"
              description="Camada estruturada de edição real conectada ao backend do módulo."
            >
              <SettingsStructuredEditor
                data={data}
                saving={saving}
                onSave={save}
              />
            </SectionBlock>
          </div>

          <div id="settings-indicator-goals">
            <SectionBlock
              title="Metas analíticas"
              description="Gestão versionada das metas reais dos indicadores por ano, vigência e ativação."
            >
              <IndicatorGoalsWorkspace getAccessToken={getAccessToken} />
            </SectionBlock>
          </div>

          <div id="settings-audit">
            <AuditWorkspacePanel getAccessToken={getAccessToken} />
          </div>
        </>
      ) : null}

      {!loading && !data && error ? (
        <InfoState
          title="Falha ao carregar configurações"
          description={error}
          actionLabel="Tentar novamente"
          onAction={() => void reload()}
        />
      ) : null}
    </div>
  );
}