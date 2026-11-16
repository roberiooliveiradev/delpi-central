import type {
  SupplierPerformance,
  SupplierPerformanceResponse,
} from "../../api/supplierPerformance";
import {
  SuppliesActionButton,
  SuppliesHostModal,
  SuppliesSectionCard,
  SuppliesStateBanner,
} from "../../app/suppliesUi";
import { PerformanceComposition } from "./PerformanceComposition";
import {
  countLabel,
  COVERAGE_LABELS,
  periodLabel,
} from "./supplierPerformancePresentation";

export function SupplierPerformanceDetail({
  item,
  data,
  onClose,
}: {
  item: SupplierPerformance | null;
  data: SupplierPerformanceResponse;
  onClose: () => void;
}) {
  if (!item) return null;
  return (
    <SuppliesHostModal
      open
      title={item.supplier_name}
      description={`Fornecedor ${item.supplier_code} · Loja ${item.supplier_store} · ${periodLabel(data.period)}`}
      onClose={onClose}
      footer={
        <SuppliesActionButton onClick={onClose}>
          Fechar detalhes
        </SuppliesActionButton>
      }
    >
      <div className="sp-idf-detail">
        <PerformanceComposition
          quality={item.quality.index}
          delivery={item.delivery.index}
          score={item.idf}
          qualityPoints={item.quality_contribution}
          deliveryPoints={item.delivery_contribution}
          weights={data.methodology}
        />
        {item.status !== "complete" ? (
          <SuppliesStateBanner>
            {COVERAGE_LABELS[item.status]}. O IDF só é calculado com as duas
            bases disponíveis e sem registros inconsistentes.
          </SuppliesStateBanner>
        ) : null}
        <div className="sp-idf-detail__bases">
          <SuppliesSectionCard title="Base de Qualidade">
            <dl className="sp-idf-facts">
              <div>
                <dt>Inspeções concluídas</dt>
                <dd>{countLabel(item.quality.assessed_count)}</dd>
              </div>
              <div>
                <dt>Aprovadas (inclui condicionais e urgentes)</dt>
                <dd>{countLabel(item.quality.positive_count)}</dd>
              </div>
              <div>
                <dt>Rejeitadas</dt>
                <dd>{countLabel(item.quality.negative_count)}</dd>
              </div>
              <div>
                <dt>Com laudo condicional</dt>
                <dd>{countLabel(item.quality.conditional_count)}</dd>
              </div>
              <div>
                <dt>Com liberação urgente</dt>
                <dd>{countLabel(item.quality.urgent_count)}</dd>
              </div>
              <div>
                <dt>Registros a revisar</dt>
                <dd>{countLabel(item.quality.unknown_count)}</dd>
              </div>
            </dl>
            <p className="sp-idf-caption">
              Data de referência: laudo. Uma inspeção é contada uma vez, mesmo
              com múltiplos ensaios.
            </p>
          </SuppliesSectionCard>
          <SuppliesSectionCard title="Base de Entrega">
            <dl className="sp-idf-facts">
              <div>
                <dt>Linhas de recebimento</dt>
                <dd>{countLabel(item.delivery.assessed_count)}</dd>
              </div>
              <div>
                <dt>No prazo ou antecipadas</dt>
                <dd>{countLabel(item.delivery.positive_count)}</dd>
              </div>
              <div>
                <dt>Fora do prazo ou sem data válida</dt>
                <dd>{countLabel(item.delivery.negative_count)}</dd>
              </div>
              <div>
                <dt>Registros sem data válida</dt>
                <dd>{countLabel(item.delivery.unknown_count)}</dd>
              </div>
            </dl>
            <p className="sp-idf-caption">
              Data de referência: digitação do recebimento. Mesmo critério do
              OTD de Suprimentos, por linha recebida, sem ponderação por
              quantidade.
            </p>
          </SuppliesSectionCard>
        </div>
        <p className="sp-idf-caption">
          Filiais com movimento: {item.branches.join(", ")}. Loja e código
          identificam o fornecedor. Contribuições são arredondadas apenas para
          exibição; o IDF usa os índices sem arredondamento intermediário.
        </p>
      </div>
    </SuppliesHostModal>
  );
}
