import { ArrowLeft } from "lucide-react";

import { EmptyState } from "../components/EmptyState";
import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS } from "../constants/branches";
import type { ScrapRegistroItem } from "../types/scrap";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatQuantity,
} from "../utils/formatters";
import { navigateScrapBack } from "../utils/navigation";
import { branchHomePath } from "../utils/routes";

type ScrapRegistroDetailPageProps = {
  branchRoute: BranchRouteCode;
  registro: ScrapRegistroItem | null;
};

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="sm-detail-grid__item">
      <dt>{label}</dt>
      <dd>{value || "—"}</dd>
    </div>
  );
}

export function ScrapRegistroDetailPage({
  branchRoute,
  registro,
}: ScrapRegistroDetailPageProps) {
  const branchLabel = BRANCH_ROUTE_LABELS[branchRoute];

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
                ? `${formatDatePtBr(registro.dataPerda)} · ${registro.mp || "MP não informada"}`
                : "Registro não encontrado na URL."}
            </p>
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
          <div className="sm-detail-layout">
            <section className="sm-card sm-detail-card">
              <header className="sm-detail-card__header">
                <h2 className="sm-detail-card__title">Identificação</h2>
              </header>
              <div className="sm-detail-card__body">
                <dl className="sm-detail-grid">
                  <DetailItem label="Filial" value={registro.filial} />
                  <DetailItem label="Data" value={formatDatePtBr(registro.dataPerda)} />
                  <DetailItem label="OP" value={registro.op} />
                  <DetailItem label="Produto acabado" value={registro.pa} />
                  <DetailItem label="Matéria-prima" value={registro.mp} />
                  <DetailItem
                    label="Descrição"
                    value={registro.descricao}
                  />
                </dl>
              </div>
            </section>

            <section className="sm-card sm-detail-card">
              <header className="sm-detail-card__header">
                <h2 className="sm-detail-card__title">Causa e operação</h2>
              </header>
              <div className="sm-detail-card__body">
                <dl className="sm-detail-grid">
                  <DetailItem label="Motivo" value={registro.motivo} />
                  <DetailItem label="Código do motivo" value={registro.motivoCodigo} />
                  <DetailItem label="Centro de trabalho" value={registro.centroTrabalho} />
                  <DetailItem label="Colaborador" value={registro.nomeOperador} />
                  <DetailItem label="Código do operador" value={registro.codigoOperador} />
                </dl>
              </div>
            </section>

            <section className="sm-card sm-detail-card sm-detail-card--wide">
              <header className="sm-detail-card__header">
                <h2 className="sm-detail-card__title">Quantidade e valor</h2>
              </header>
              <div className="sm-detail-card__body">
                <dl className="sm-detail-grid">
                  <DetailItem
                    label="Quantidade"
                    value={`${formatQuantity(registro.quantidade)}${registro.um ? ` ${registro.um}` : ""}`}
                  />
                  <DetailItem label="Valor" value={formatCurrencyBrl(registro.valor)} />
                </dl>
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
