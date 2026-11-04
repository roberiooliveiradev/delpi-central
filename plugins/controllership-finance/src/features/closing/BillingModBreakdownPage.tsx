/**
 * R09 — Faturamento × MOD (DLP204 reconstruído) — visão operacional.
 *
 * Mostra o que as fontes Protheus hoje comprovam: âncoras PA faturadas,
 * linhas MOD por nível/roteiro, quantidades e horas — com divergências
 * históricas, ausências tipadas e paridade oficial pendente explícitas.
 */
import { useEffect, useState } from "react";

import {
  CfEmptyState,
  CfSectionCard,
  CfSelectField,
  CfStateBanner,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  getBillingModBreakdown,
  type BillingModAnchor,
  type BillingModBreakdownPayload,
  type TypedNumber,
} from "../../api/billingModBreakdownApi";

type AsyncData =
  | null
  | { kind: "error"; error: { status?: number; message?: string } }
  | { kind: "data"; data: BillingModBreakdownPayload };

const BRANCH_OPTIONS = [
  { value: "all", label: "Filiais 01 + 02" },
  { value: "01", label: "Filial 01" },
  { value: "02", label: "Filial 02" },
];

function fmtNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("pt-BR", {
    maximumFractionDigits: 4,
  });
}

function fmtTyped(num: TypedNumber | undefined): string {
  if (!num) return "—";
  if (num.value === null || num.value === undefined) return "indisponível";
  return fmtNumber(num.value);
}

export function BillingModBreakdownPage({
  reportContext,
}: {
  reportContext: { period: string };
}) {
  const period = reportContext.period;
  const [branch, setBranch] = useState("all");
  const [state, setState] = useState<AsyncData>(null);

  useEffect(() => {
    let active = true;
    setState(null);
    getBillingModBreakdown(period, branch)
      .then((data) => {
        if (active) setState({ kind: "data", data });
      })
      .catch((error) => {
        if (active) setState({ kind: "error", error });
      });
    return () => {
      active = false;
    };
  }, [period, branch]);

  return (
    <div className="cf-page-stack" aria-label="Faturamento × MOD">
      <CfStateBanner>
        <p className="cf-banner-title">
          Visão operacional — paridade oficial pendente
        </p>
        <p className="cf-banner-text">
          Os dados são obtidos das fontes atualmente disponíveis do
          Protheus. Existem diferenças conhecidas em relação ao relatório
          histórico DLP204, especialmente em roteiros, quantidades e
          horas. A taxa histórica de MOD não foi comprovada — custos
          dependentes dela não são apresentados.
        </p>
      </CfStateBanner>

      <CfSectionCard title="Filtros">
        <div className="cf-r09-filter">
          <CfSelectField
          label="Filial"
          value={branch}
          options={BRANCH_OPTIONS}
          onChange={(value) => setBranch(value)}
          />
        </div>
      </CfSectionCard>

      {state === null ? (
        <p aria-live="polite">Carregando faturamento × MOD…</p>
      ) : state.kind === "error" ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage={`Não foi possível carregar o relatório R09${
            state.error?.message ? ` — ${state.error.message}` : ""
          }.`}
        />
      ) : state.data.anchors.length === 0 ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage="Nenhuma âncora faturada encontrada para a competência/filial selecionadas."
        />
      ) : (
        <AnchorsSection payload={state.data} />
      )}
    </div>
  );
}

function AnchorsSection({
  payload,
}: {
  payload: BillingModBreakdownPayload;
}) {
  return (
    <>
      {payload.parityEvidence ? (
        <CfSectionCard title="Evidência histórica de paridade">
          <p className="cf-muted">
            {payload.parityEvidence.semantics}
          </p>
          <ul className="cf-muted">
            <li>
              Referência: {payload.parityEvidence.scope.referencePeriod}{" "}
              ({payload.parityEvidence.scope.artifact})
            </li>
            <li>
              Chaves correspondentes: {payload.parityEvidence.metrics.matchedKeys}
              /{payload.parityEvidence.metrics.artifactLines} (
              {payload.parityEvidence.metrics.keyCoveragePct}%)
            </li>
            <li>
              Homologação: {payload.parityEvidence.scope.homologationStatus}
            </li>
          </ul>
        </CfSectionCard>
      ) : null}

      {payload.limitations?.length ? (
        <CfSectionCard title="Limitações e divergências conhecidas">
          <ul className="cf-muted">
            {payload.limitations.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </CfSectionCard>
      ) : null}

      {payload.anchors.map((anchor, index) => (
        <AnchorCard key={`${anchor.product}-${index}`} anchor={anchor} />
      ))}
    </>
  );
}

function AnchorCard({ anchor }: { anchor: BillingModAnchor }) {
  return (
    <CfSectionCard
      title={`${anchor.product}${
        anchor.productDescription
          ? ` — ${anchor.productDescription}`
          : ""
      }`}
    >
      <p className="cf-muted">
        Qtd faturada: {fmtNumber(anchor.billedQty)}
        {anchor.branch ? ` · Filial ${anchor.branch}` : ""}
      </p>
      {anchor.modLines.length === 0 ? (
        <p className="cf-muted">
          Sem linhas MOD — produto sem roteiro/recurso MOD mapeado.
        </p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="cf-data-table">
            <thead>
              <tr>
                <th>Nível</th>
                <th>Produto</th>
                <th>Operação</th>
                <th>Recurso</th>
                <th>Item MOD</th>
                <th>Qtd propagada</th>
                <th>Tempo</th>
                <th>Horas</th>
                <th>Custo unit.</th>
                <th>Custo total</th>
              </tr>
            </thead>
            <tbody>
              {anchor.modLines.map((line, index) => (
                <tr key={index}>
                  <td>{line.level}</td>
                  <td>{line.product ?? "—"}</td>
                  <td>
                    {line.operationDescription ??
                      line.operation ??
                      "—"}
                  </td>
                  <td>{line.resource ?? "—"}</td>
                  <td>{line.modItem ?? "—"}</td>
                  <td>{fmtNumber(line.propagatedQty)}</td>
                  <td>{fmtTyped(line.stdTime)}</td>
                  <td>{fmtTyped(line.hours)}</td>
                  <td>{fmtTyped(line.costUnit)}</td>
                  <td>{fmtTyped(line.costTotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </CfSectionCard>
  );
}
