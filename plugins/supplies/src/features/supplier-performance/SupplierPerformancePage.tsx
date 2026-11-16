import { useState } from "react";
import { ClipboardCheck, RefreshCw, Truck, Users } from "lucide-react";
import type { SupplierPerformance } from "../../api/supplierPerformance";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesMetricCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { OverviewFilters } from "../overview/OverviewFilters";
import { useOverviewFilters } from "../overview/useOverviewFilters";
import { PerformanceComposition } from "./PerformanceComposition";
import { SupplierPerformanceDetail } from "./SupplierPerformanceDetail";
import { SupplierPerformanceTable } from "./SupplierPerformanceTable";
import {
  countLabel,
  periodLabel,
  supplierKey,
} from "./supplierPerformancePresentation";
import { useSupplierPerformance } from "./useSupplierPerformance";
import "./supplierPerformance.css";

export function SupplierPerformancePage({ basePath }: { basePath: string }) {
  const session = useSuppliesSession();
  const filters = useOverviewFilters(session.allowedUnits);
  const { data, loading, error, reload } = useSupplierPerformance(
    filters.apiParams,
  );
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const selected =
    data?.items.find((item) => supplierKey(item) === selectedKey) ?? null;
  const openDetails = (item: SupplierPerformance) =>
    setSelectedKey(supplierKey(item));
  const summary = data?.summary;

  return (
    <div className="sp-page-stack sp-idf-page">
      <SuppliesPagePath
        back={{
          label: "Visão geral",
          href: buildPluginPath("overview", basePath),
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("overview", { basePath });
          },
        }}
        items={[]}
        current="IDF dos fornecedores"
      />
      <SuppliesPageHero
        eyebrow="ANÁLISES · FORNECEDORES"
        title="IDF dos fornecedores"
        description="Qualidade e pontualidade reunidas para acompanhar quem fornece à DELPI."
        badge={
          <SuppliesStatusBadge label={filters.scopeBadge} variant="info" />
        }
        actions={
          <SuppliesActionButton onClick={reload} disabled={loading}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </SuppliesActionButton>
        }
      >
        <OverviewFilters
          period={filters.period}
          from={filters.from}
          to={filters.to}
          branches={filters.branches}
          unitOptions={filters.unitOptions}
          onPeriod={filters.setPeriod}
          onFrom={filters.setFrom}
          onTo={filters.setTo}
          onBranches={filters.setBranches}
        />
      </SuppliesPageHero>

      {loading ? (
        <SuppliesLoadingCard
          title="Consultando Qualidade e Entrega…"
          variant="panel"
        />
      ) : error ? (
        <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
      ) : data && summary ? (
        <>
          {summary.suppliers === 0 ? (
            <SuppliesEmptyState
              title="Sem movimento neste período"
              message="Não encontramos inspeções concluídas ou recebimentos no recorte selecionado. Amplie o período ou ajuste as filiais."
            />
          ) : (
            <>
              <SuppliesSectionCard
                title="Desempenho no período"
                hint="Média simples dos IDFs dos fornecedores com as duas bases disponíveis. Cada código e loja tem o mesmo peso; fornecedores incompletos ficam fora da média."
              >
                <PerformanceComposition
                  quality={summary.average_quality}
                  delivery={summary.average_delivery}
                  score={summary.average_idf}
                  weights={data.methodology}
                />
                <div className="sp-idf-period-note">
                  <span>
                    Média de {countLabel(summary.evaluated)} de{" "}
                    {countLabel(summary.suppliers)} fornecedores
                  </span>
                  <span>{periodLabel(data.period)}</span>
                </div>
              </SuppliesSectionCard>
              <div className="sp-idf-metrics">
                <SuppliesMetricCard
                  label="Fornecedores avaliados"
                  value={countLabel(summary.evaluated)}
                  hint={`${countLabel(summary.incomplete)} com base incompleta`}
                  icon={<Users size={20} aria-hidden="true" />}
                />
                <SuppliesMetricCard
                  label="Inspeções concluídas"
                  value={countLabel(summary.inspection_count)}
                  hint="Pela data do laudo · base total"
                  icon={<ClipboardCheck size={20} aria-hidden="true" />}
                />
                <SuppliesMetricCard
                  label="Linhas recebidas"
                  value={countLabel(summary.receipt_count)}
                  hint="Pela digitação do recebimento · base total"
                  icon={<Truck size={20} aria-hidden="true" />}
                />
              </div>
              {summary.incomplete > 0 ? (
                <SuppliesStateBanner>
                  {countLabel(summary.incomplete)} fornecedor(es) com dados
                  incompletos. Consulte a disponibilidade na lista para entender
                  qual base falta; esses fornecedores não entram na média.
                </SuppliesStateBanner>
              ) : null}
              <SuppliesSectionCard
                title="Desempenho por fornecedor"
                hint="IDF de 0 a 100. Código e loja identificam cada fornecedor; a consolidação das filiais soma as contagens antes de calcular os índices."
              >
                <SupplierPerformanceTable
                  key={`${data.period.from}:${data.period.to}:${data.branches.join(",")}`}
                  items={data.items}
                  onSelect={openDetails}
                />
              </SuppliesSectionCard>
              <p className="sp-idf-caption">
                Base consultada em{" "}
                {new Date(data.calculated_at).toLocaleString("pt-BR", {
                  timeZone: "America/Sao_Paulo",
                })}{" "}
                (Brasília). Cache configurável: padrão de 5 minutos.
              </p>
            </>
          )}
          <SupplierPerformanceDetail
            item={loading ? null : selected}
            data={data}
            onClose={() => setSelectedKey(null)}
          />
        </>
      ) : null}
      <SuppliesSectionCard
        title="Como o IDF é calculado"
        collapsible
        defaultOpen={false}
      >
        <div className="sp-idf-methodology">
          <p>
            <strong>IDF = (Qualidade × 0,70) + (Entrega × 0,30).</strong> Os
            dois índices usam a escala de 0 a 100.
          </p>
          <p>
            <strong>Qualidade:</strong> inspeções aprovadas ÷ inspeções
            concluídas × 100, pela data do laudo. Mantém o critério atual do
            Portal: aprovado, liberação urgente e laudo condicional contam como
            aprovação. O detalhe mostra essas ocorrências separadamente.
          </p>
          <p>
            <strong>Entrega:</strong> linhas de recebimento no prazo ou
            antecipadas ÷ linhas recebidas × 100, pela data de digitação. Uma
            entrega parcial pode gerar mais de uma linha; não é uma contagem de
            pedidos nem uma ponderação por quantidade.
          </p>
          <p>
            <strong>Escopo:</strong> matérias-primas e produtos da família 3019,
            como no OTD de Suprimentos. Qualidade e Entrega são eventos
            distintos no período; suas contagens podem ser diferentes.
          </p>
          <p>
            <strong>Sem base completa:</strong> mostramos os índices disponíveis
            e deixamos o IDF sem nota. Faixas de classificação e metas dependem
            de definição por Suprimentos e Qualidade; esta tela não atribui
            conceitos de bom ou ruim.
          </p>
        </div>
      </SuppliesSectionCard>
    </div>
  );
}
