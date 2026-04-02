import { Card } from "../components/Card";
import { InfoState } from "../components/InfoState";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";

export function ExecutiveDashboardPage() {
  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Strategic Indicators"
        description="Base visual do módulo preparada para evoluir para a visão executiva do IGD, dos IDDs departamentais e dos indicadores estratégicos."
        badge={<StatusBadge label="Fundação visual" variant="info" />}
      />

      <SectionBlock
        title="Estado atual do módulo"
        description="Esta etapa consolida a fundação visual do plugin e prepara a interface para a próxima fase do roadmap."
      >
        <div className="si-grid si-grid--hero">
          <Card
            title="Microfrontend validado"
            description="A integração federada com a MinhaDelpi foi concluída com sucesso."
            headerRight={<StatusBadge label="Operacional" variant="success" />}
          >
            <InfoState
              title="Plugin carregado com sucesso"
              description="A casca visual do Strategic Indicators já está pronta. O próximo passo será construir a visão executiva do dashboard."
            />
          </Card>

          <Card
            title="Próxima evolução"
            description="Na Fase 3, esta área receberá os blocos reais da visão executiva."
            headerRight={<StatusBadge label="Próxima etapa" variant="warning" />}
          >
            <ul className="si-list">
              <li>Hero do IGD</li>
              <li>Faixa de classificação</li>
              <li>Cards dos departamentos</li>
              <li>Tendência do IGD</li>
              <li>Contribuição por área</li>
            </ul>
          </Card>
        </div>
      </SectionBlock>

      <SectionBlock
        title="Estrutura preparada"
        description="A linguagem visual abaixo estabelece o padrão dos blocos que serão reutilizados no restante do plugin."
      >
        <div className="si-grid si-grid--cards">
          <Card
            title="Cards base"
            description="Estrutura reutilizável para KPIs, indicadores e agrupamentos visuais."
          >
            <p className="si-muted">
              O componente Card será reutilizado em resumos, agrupamentos e
              blocos analíticos do dashboard.
            </p>
          </Card>

          <Card
            title="Badges semânticos"
            description="Estados visuais padronizados para informação, sucesso, alerta e risco."
            headerRight={<StatusBadge label="Padrão ativo" variant="neutral" />}
          >
            <div className="si-badge-row">
              <StatusBadge label="Info" variant="info" />
              <StatusBadge label="Sucesso" variant="success" />
              <StatusBadge label="Alerta" variant="warning" />
              <StatusBadge label="Risco" variant="danger" />
            </div>
          </Card>

          <Card
            title="Seções escaláveis"
            description="Organização visual pronta para crescer com o roadmap."
          >
            <p className="si-muted">
              A página já está estruturada para receber blocos executivos,
              tendências, indicadores e alertas sem retrabalho estrutural.
            </p>
          </Card>
        </div>
      </SectionBlock>
    </div>
  );
}