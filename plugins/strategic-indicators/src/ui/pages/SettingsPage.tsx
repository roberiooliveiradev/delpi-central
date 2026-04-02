import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { SettingsActionPanel } from "../components/SettingsActionPanel";
import { SettingsEditorPanel } from "../components/SettingsEditorPanel";
import { SettingsExecutiveHighlight } from "../components/SettingsExecutiveHighlight";
import { SettingsGoalsPanel } from "../components/SettingsGoalsPanel";
import { SettingsGovernancePanel } from "../components/SettingsGovernancePanel";
import { SettingsHero } from "../components/SettingsHero";
import { SettingsParametersPanel } from "../components/SettingsParametersPanel";
import { SettingsReadinessPanel } from "../components/SettingsReadinessPanel";
import { SettingsSummaryCards } from "../components/SettingsSummaryCards";
import { SettingsWeightsPanel } from "../components/SettingsWeightsPanel";
import { StatusBadge } from "../components/StatusBadge";
import { useStrategicIndicatorsSettings } from "../../state/hooks/useStrategicIndicatorsSettings";

import type {
  SettingsDashboardData,
  SettingsReadinessItem,
} from "../../data/mocks/settingsMock";

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

export function SettingsPage({ getAccessToken }: SettingsPageProps) {
  const {
    data,
    loading,
    saving,
    error,
    successMessage,
    save,
    reload,
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
        description="Camada administrativa inicial do módulo, organizada para futura persistência real de pesos, metas e parâmetros."
        badge={<StatusBadge label="MVP Governança" variant="neutral" />}
      />

      <SettingsHero
        routePath="/apps/strategic-indicators/settings"
        permissionCode="strategic-indicators.settings.manage"
      />

      {loading ? (
        <div className="si-settings-feedback">Carregando configurações reais...</div>
      ) : null}

      {error ? (
        <div className="si-settings-feedback si-settings-feedback--error">
          {error}
          <button
            type="button"
            className="si-settings-feedback__button"
            onClick={() => void reload()}
          >
            Tentar novamente
          </button>
        </div>
      ) : null}

      {successMessage ? (
        <div className="si-settings-feedback si-settings-feedback--success">
          {successMessage}
        </div>
      ) : null}

      {!loading && data && settingsDashboardData ? (
        <>
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

          <SectionBlock
            title="Parâmetros globais"
            description="Elementos estruturais do módulo que definem a leitura oficial do painel."
          >
            <SettingsParametersPanel items={settingsDashboardData.parameters} />
          </SectionBlock>

          <SectionBlock
            title="Pesos oficiais"
            description="Composição governada do IGD conforme o documento consolidado."
          >
            <SettingsWeightsPanel items={settingsDashboardData.weights} />
          </SectionBlock>

          <SectionBlock
            title="Metas resumidas"
            description="Referências executivas das metas mais importantes por área."
          >
            <SettingsGoalsPanel items={settingsDashboardData.goals} />
          </SectionBlock>

          <SectionBlock
            title="Governança do módulo"
            description="Parâmetros administrativos e observações da fase atual do painel."
          >
            <SettingsGovernancePanel items={settingsDashboardData.governance} />
          </SectionBlock>

          <SectionBlock
            title="Prontidão administrativa"
            description="Leitura do que já está pronto e do que ainda evoluirá para persistência real."
          >
            <SettingsReadinessPanel items={readinessItems} />
          </SectionBlock>

          <SectionBlock
            title="Próxima ação"
            description="Resumo do próximo passo administrativo mais natural do módulo."
          >
            <SettingsActionPanel data={settingsDashboardData} />
          </SectionBlock>

          <SectionBlock
            title="Edição inicial"
            description="Primeira camada de edição real conectada ao backend do módulo."
          >
            <SettingsEditorPanel
              data={data}
              saving={saving}
              onSave={save}
            />
          </SectionBlock>
        </>
      ) : null}
    </div>
  );
}