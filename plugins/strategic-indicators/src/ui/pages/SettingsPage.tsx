import { settingsMock } from "../../data/mocks/settingsMock";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { SettingsActionPanel } from "../components/SettingsActionPanel";
import { SettingsExecutiveHighlight } from "../components/SettingsExecutiveHighlight";
import { SettingsGoalsPanel } from "../components/SettingsGoalsPanel";
import { SettingsGovernancePanel } from "../components/SettingsGovernancePanel";
import { SettingsHero } from "../components/SettingsHero";
import { SettingsParametersPanel } from "../components/SettingsParametersPanel";
import { SettingsReadinessPanel } from "../components/SettingsReadinessPanel";
import { SettingsSummaryCards } from "../components/SettingsSummaryCards";
import { SettingsWeightsPanel } from "../components/SettingsWeightsPanel";
import { StatusBadge } from "../components/StatusBadge";

export function SettingsPage() {
  const data = settingsMock;

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

      <SectionBlock
        title="Destaque administrativo"
        description="Síntese executiva da governança estrutural do módulo."
      >
        <SettingsExecutiveHighlight data={data} />
      </SectionBlock>

      <SectionBlock
        title="Síntese administrativa"
        description="Resumo rápido do estado de governança do módulo nesta fase."
      >
        <SettingsSummaryCards data={data} />
      </SectionBlock>

      <SectionBlock
        title="Parâmetros globais"
        description="Elementos estruturais do módulo que definem a leitura oficial do painel."
      >
        <SettingsParametersPanel items={data.parameters} />
      </SectionBlock>

      <SectionBlock
        title="Pesos oficiais"
        description="Composição governada do IGD conforme o documento consolidado."
      >
        <SettingsWeightsPanel items={data.weights} />
      </SectionBlock>

      <SectionBlock
        title="Metas resumidas"
        description="Referências executivas das metas mais importantes por área."
      >
        <SettingsGoalsPanel items={data.goals} />
      </SectionBlock>

      <SectionBlock
        title="Governança do módulo"
        description="Parâmetros administrativos e observações da fase atual do painel."
      >
        <SettingsGovernancePanel items={data.governance} />
      </SectionBlock>

      <SectionBlock
        title="Prontidão administrativa"
        description="Leitura do que já está pronto e do que ainda evoluirá para persistência real."
      >
        <SettingsReadinessPanel items={data.readiness} />
      </SectionBlock>

      <SectionBlock
        title="Próxima ação"
        description="Resumo do próximo passo administrativo mais natural do módulo."
      >
        <SettingsActionPanel data={data} />
      </SectionBlock>
    </div>
  );
}