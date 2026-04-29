import { useRef, useState } from "react";
import type { StrategicIndicatorsAuditEntityKey } from "../../data/types/settingsAudit";
import { useStrategicIndicatorsSettingsAudit } from "../../state/hooks/useStrategicIndicatorsSettingsAudit";
import { SectionBlock } from "./SectionBlock";
import { AuditSummaryPanel } from "./AuditSummaryPanel";
import { AuditLatestByEntityPanel } from "./AuditLatestByEntityPanel";
import { AuditTimelinePanel } from "./AuditTimelinePanel";
import { ChangeRequestsWorkspacePanel } from "./ChangeRequestsWorkspacePanel";
import "./AuditWorkspacePanel.css";

type AuditWorkspacePanelProps = {
  getAccessToken?: () => string | undefined;
};

export function AuditWorkspacePanel({
  getAccessToken,
}: AuditWorkspacePanelProps) {
  const audit = useStrategicIndicatorsSettingsAudit({ getAccessToken });

  const [activeAuditEntityKey, setActiveAuditEntityKey] = useState<
    "all" | StrategicIndicatorsAuditEntityKey
  >("all");

  const auditSectionRef = useRef<HTMLDivElement | null>(null);

  function focusAuditEntity(
    value: "all" | StrategicIndicatorsAuditEntityKey,
  ) {
    setActiveAuditEntityKey(value);

    requestAnimationFrame(() => {
      auditSectionRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  return (
    <>
      <SectionBlock
        title="Resumo da auditoria"
        description="Visão rápida da distribuição dos eventos administrativos recentes."
      >
        <AuditSummaryPanel
          items={audit.items}
          activeEntityKey={activeAuditEntityKey}
          onSelectEntityKey={focusAuditEntity}
        />
      </SectionBlock>

      <SectionBlock
        title="Última alteração por bloco"
        description="Leitura rápida da alteração mais recente registrada para cada grupo administrativo."
      >
        <AuditLatestByEntityPanel
          items={audit.items}
          activeEntityKey={activeAuditEntityKey}
          onSelectEntityKey={focusAuditEntity}
        />
      </SectionBlock>

      <div ref={auditSectionRef}>
        <SectionBlock
          title="Auditoria administrativa"
          description="Histórico consultável das alterações do módulo, com filtros, busca e navegação contextual."
        >
          <AuditTimelinePanel
            items={audit.items}
            loading={audit.loading}
            error={audit.error}
            initialEntityKey={activeAuditEntityKey}
            onEntityKeyChange={setActiveAuditEntityKey}
            onReload={audit.reload}
          />
        </SectionBlock>
      </div>
      <SectionBlock
        title="Solicitações administrativas"
        description="Camada preparatória para futuros workflows de aprovação, mantendo a governança do módulo sem abrir o workflow completo ainda."
      >
        <ChangeRequestsWorkspacePanel getAccessToken={getAccessToken} />
      </SectionBlock>
    </>
  );
}