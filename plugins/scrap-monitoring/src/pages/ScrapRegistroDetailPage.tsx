import {
  ArrowLeft,
  CircleDollarSign,
  ClipboardList,
  Package,
  TriangleAlert,
} from "lucide-react";

import { DetailCard, DetailFieldGrid } from "../components/detailUi";
import { EmptyState } from "../components/EmptyState";
import { KpiCard } from "../components/KpiCard";
import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS } from "../constants/branches";
import { SCRAP_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ScrapRegistroItem } from "../types/scrap";
import {
  formatCodeWithLabel,
  formatCurrencyBrl,
  formatDatePtBr,
  formatQuantity,
  resolveUnitCost,
} from "../utils/formatters";
import { navigateScrapBack } from "../utils/navigation";
import { branchHomePath } from "../utils/routes";

type ScrapRegistroDetailPageProps = {
  branchRoute: BranchRouteCode;
  registro: ScrapRegistroItem | null;
};

const D = SCRAP_HELP_TOOLTIPS.detail;

function filialLabel(filial: string, branchRoute: BranchRouteCode): string {
  const code = filial.trim() || (branchRoute === "ES" ? "02" : "01");
  const name = code === "02" ? "ES" : code === "01" ? "SC" : BRANCH_ROUTE_LABELS[branchRoute];
  return `${code} (${name})`;
}

export function ScrapRegistroDetailPage({
  branchRoute,
  registro,
}: ScrapRegistroDetailPageProps) {
  const branchLabel = BRANCH_ROUTE_LABELS[branchRoute];
  const unitCost = registro
    ? resolveUnitCost(registro.valor, registro.quantidade, registro.custoUnitario)
    : null;
  const withoutCost = Boolean(registro && (registro.valor === 0 || unitCost === 0 || unitCost == null));

  return (
    <div className="dashboard-scrap-monitoring dashboard-page sm-page">
      <div className="sm-app-shell sm-detail-page">
        <header className="sm-detail-page__header">
          <div>
            <p className="sm-detail-page__eyebrow">Acompanhamento de Refugos — {branchLabel}</p>
            <h1 className="sm-detail-page__title">
              Detalhe do refugo
              {registro?.op ? (
                <span className="sm-detail-page__meta">OP {registro.op}</span>
              ) : null}
            </h1>
            <p className="sm-detail-page__subtitle">
              {registro
                ? `${formatDatePtBr(registro.dataPerda)} · MP ${registro.mp || "não informada"}${
                    registro.centroTrabalho ? ` · ${registro.centroTrabalho}` : ""
                  }`
                : "Registro não encontrado na URL."}
            </p>
            {registro?.motivo ? (
              <div className="sm-detail-page__tags" aria-label="Resumo do apontamento">
                <span className="sm-detail-tag">{registro.motivo}</span>
                {registro.centroTrabalho ? (
                  <span className="sm-detail-tag sm-detail-tag--muted">
                    {registro.centroTrabalho}
                  </span>
                ) : null}
                {withoutCost ? (
                  <span className="sm-detail-tag sm-detail-tag--warning">Sem custo unitário</span>
                ) : null}
              </div>
            ) : null}
          </div>
          <button
            type="button"
            className="sm-btn sm-btn--secondary"
            onClick={() => navigateScrapBack(branchHomePath(branchRoute))}
          >
            <ArrowLeft size={16} aria-hidden />
            Voltar
          </button>
        </header>

        {!registro ? (
          <EmptyState
            title="Registro indisponível"
            message="Não foi possível carregar os dados deste refugo. Volte à lista e selecione novamente."
          />
        ) : (
          <>
            <div className="sm-detail-kpi-grid">
              <KpiCard
                title="Valor do refugo"
                titleHint={D.financial}
                value={formatCurrencyBrl(registro.valor)}
                icon={<CircleDollarSign size={22} />}
              />
              <KpiCard
                title="Quantidade"
                value={`${formatQuantity(registro.quantidade)}${registro.um ? ` ${registro.um}` : ""}`}
                icon={<Package size={22} />}
              />
              <KpiCard
                title="Custo unitário"
                titleHint={D.unitCost}
                value={unitCost == null ? "—" : formatCurrencyBrl(unitCost)}
                icon={
                  withoutCost ? <TriangleAlert size={22} /> : <ClipboardList size={22} />
                }
              />
            </div>

            <div className="sm-detail-layout">
              <DetailCard title="Identificação" titleHint={D.identification}>
                <DetailFieldGrid
                  fields={[
                    { label: "Filial", value: filialLabel(registro.filial, branchRoute) },
                    { label: "Data", value: formatDatePtBr(registro.dataPerda) },
                    { label: "Ordem de produção", value: registro.op || "—" },
                    {
                      label: "Centro de trabalho",
                      value: registro.centroTrabalho || "—",
                    },
                  ]}
                />
              </DetailCard>

              <DetailCard title="Causa e operação" titleHint={D.cause}>
                <DetailFieldGrid
                  fields={[
                    { label: "Motivo", value: registro.motivo || "—", wide: true },
                    { label: "Código do motivo", value: registro.motivoCodigo || "—" },
                    {
                      label: "Colaborador",
                      value: registro.nomeOperador || "—",
                      wide: true,
                    },
                    {
                      label: "Código do operador",
                      value: registro.codigoOperador || "—",
                    },
                  ]}
                />
              </DetailCard>

              <DetailCard
                title="Produtos"
                titleHint={D.product}
                className="sm-detail-card--full"
              >
                <DetailFieldGrid
                  fields={[
                    {
                      label: "Matéria-prima",
                      value: formatCodeWithLabel(registro.mp, registro.descricao),
                      wide: true,
                    },
                    {
                      label: "Produto acabado",
                      value: formatCodeWithLabel(registro.pa, registro.paDescricao),
                      wide: true,
                    },
                    {
                      label: "Unidade de medida",
                      value: registro.um || "—",
                    },
                    {
                      label: "Valor total",
                      value: formatCurrencyBrl(registro.valor),
                    },
                  ]}
                />
              </DetailCard>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
