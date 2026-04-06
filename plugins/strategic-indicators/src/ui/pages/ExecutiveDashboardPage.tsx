import { executiveDashboardMock } from "../../data/mocks/executiveDashboardMock";
import { Card } from "../components/Card";
import { ClassificationBand } from "../components/ClassificationBand";
import { ContributionRanking } from "../components/ContributionRanking";
import { DepartmentSummaryGrid } from "../components/DepartmentSummaryGrid";
import { ExecutiveMethodCard } from "../components/ExecutiveMethodCard";
import { IgdHeroCard } from "../components/IgdHeroCard";
import { PageHeader } from "../components/PageHeader";
import { SectionBlock } from "../components/SectionBlock";
import { StatusBadge } from "../components/StatusBadge";

type ExecutiveDashboardPageProps = {
  getAccessToken?: () => string | undefined;
};

export function ExecutiveDashboardPage({
  getAccessToken,
}: ExecutiveDashboardPageProps) {
  void getAccessToken;

  const data = executiveDashboardMock;

  const strongestDepartment = [...data.departments].sort(
    (a, b) => b.score - a.score,
  )[0];

  const watchDepartment = [...data.departments].sort(
    (a, b) => a.score - b.score,
  )[0];

  const totalContribution = data.departments.reduce(
    (sum, department) => sum + department.contribution,
    0,
  );

  return (
    <div className="si-page">
      <PageHeader
        eyebrow="MinhaDelpi"
        title="Strategic Indicators"
        description="Painel executivo inicial do IGD e dos IDDs departamentais, estruturado para evoluir com tendências, alertas e análise detalhada."
        badge={<StatusBadge label="MVP Executivo" variant="info" />}
      />

      <div className="si-executive-grid">
        <IgdHeroCard
          igd={data.igd}
          igdExact={data.igdExact}
          classification={data.classification}
          strongestDepartment={`${strongestDepartment.name} (${strongestDepartment.score.toFixed(1)})`}
          watchDepartment={`${watchDepartment.name} (${watchDepartment.score.toFixed(1)})`}
        />

        <Card
          title="Leitura executiva"
          description="O índice resume, em uma nota única, a performance integrada das áreas estratégicas da empresa."
          headerRight={<StatusBadge label="Mensal" variant="neutral" />}
        >
          <p className="si-muted">
            O valor exibido neste MVP usa o exemplo oficial do documento-base e
            já respeita a lógica de consolidação executiva do índice global.
          </p>

          <div className="si-executive-note">
            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Faixa atual</span>
              <strong className="si-executive-note__value">
                {data.classification}
              </strong>
            </div>

            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Melhor IDD</span>
              <strong className="si-executive-note__value">
                {strongestDepartment.name}
              </strong>
            </div>

            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Atenção prioritária</span>
              <strong className="si-executive-note__value">
                {watchDepartment.name}
              </strong>
            </div>

            <div className="si-executive-note__item">
              <span className="si-executive-note__label">Soma ponderada</span>
              <strong className="si-executive-note__value">
                {totalContribution.toFixed(3)}
              </strong>
            </div>
          </div>
        </Card>
      </div>

      <SectionBlock
        title="Faixa interpretativa do IGD"
        description="A régua abaixo traduz a nota do índice em leitura gerencial objetiva."
      >
        <ClassificationBand value={data.igd} />
      </SectionBlock>

      <SectionBlock
        title="Metodologia do índice"
        description="Resumo visual de como o índice global é consolidado no painel estratégico."
      >
        <ExecutiveMethodCard igdExact={data.igdExact} />
      </SectionBlock>

      <SectionBlock
        title="Contribuição por departamentos"
        description="O ranking abaixo mostra como cada área participa da composição ponderada do IGD."
      >
        <ContributionRanking departments={data.departments} />
      </SectionBlock>

      <SectionBlock
        title="Composição por departamentos"
        description="Os cards abaixo mostram os departamentos que compõem o IGD, com seus pesos oficiais, nota resumida, foco estratégico e metas de referência do modelo 2026."
      >
        <DepartmentSummaryGrid departments={data.departments} />
      </SectionBlock>
    </div>
  );
}