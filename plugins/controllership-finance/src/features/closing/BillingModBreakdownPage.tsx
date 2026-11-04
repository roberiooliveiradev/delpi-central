/**
 * R09 — Faturamento × MOD (DLP204 reconstruído) — visão operacional.
 *
 * Redesign doc 153: hero `ClosingHero` + indicadores reais + tabela
 * master `DataTableSection` (âncora produto+filial) com detalhe inline
 * das operações MOD — substitui a lista de cards gigantes por âncora.
 * Ausências tipadas nunca são zero; paridade oficial pendente (DR-3);
 * evidência DLP204 permanece histórica e datada (ref. 09/2026), nunca
 * como selo da competência corrente.
 */
import { useCallback, useMemo, useState, useEffect } from "react";

import { ClosingHero } from "../../app/ClosingHero";
import {
  CfActionButton,
  CfEmptyState,
  CfSectionCard,
  CfSelectField,
  CfStateBanner,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import {
  getBillingModBreakdown,
  type BillingModAnchor,
  type BillingModBreakdownPayload,
  type BillingModLine,
  type TypedNumber,
} from "../../api/billingModBreakdownApi";
import { CF_HELP } from "../../content/helpTooltips";

type AsyncData =
  | null
  | { kind: "error"; error: { status?: number; message?: string } }
  | { kind: "data"; data: BillingModBreakdownPayload };

const BRANCH_OPTIONS = [
  { value: "all", label: "Filiais 01 + 02" },
  { value: "01", label: "Filial 01" },
  { value: "02", label: "Filial 02" },
];

/** Chave estável da âncora: grão físico = filial + produto. */
function anchorKey(anchor: BillingModAnchor): string {
  return `${anchor.branch ?? "—"}::${anchor.product}`;
}

function fmtNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("pt-BR", {
    maximumFractionDigits: 4,
  });
}

/** `TypedNumber.state` é string aberta — rótulos só para estados
 *  mapeados; fallback neutro para desconhecidos. Nunca null → 0. */
const TYPED_STATE_LABELS: Record<string, string> = {
  AVAILABLE: "disponível",
  SOURCE_MISSING: "fonte ausente",
  MISSING: "ausente",
  UNAVAILABLE: "indisponível",
  NOT_APPLICABLE: "não aplicável",
  PENDING: "pendente de fonte",
};

function fmtTyped(num: TypedNumber | undefined): string {
  if (!num) return "—";
  if (num.value !== null && num.value !== undefined) {
    return fmtNumber(num.value);
  }
  return TYPED_STATE_LABELS[num.state] ?? "não informado pela fonte";
}

export function BillingModBreakdownPage({
  reportContext,
}: {
  reportContext: { period: string };
}) {
  const period = reportContext.period;
  const [branch, setBranch] = useState("all");
  const [reloadToken, setReloadToken] = useState(0);
  const [state, setState] = useState<AsyncData>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const load = useCallback(() => setReloadToken((t) => t + 1), []);

  useEffect(() => {
    let active = true;
    setState(null);
    getBillingModBreakdown(period, branch)
      .then((data) => {
        if (active) {
          setState({ kind: "data", data });
          setUpdatedAt(new Date());
        }
      })
      .catch((error) => {
        if (active) setState({ kind: "error", error });
      });
    return () => {
      active = false;
    };
  }, [period, branch, reloadToken]);

  const payload = state?.kind === "data" ? state.data : null;
  const loading = state === null;

  const metrics = useMemo(() => {
    if (!payload) return undefined;
    const totalLines = payload.anchors.reduce(
      (sum, anchor) => sum + anchor.modLines.length,
      0,
    );
    const withoutLines = payload.anchors.filter(
      (anchor) => anchor.modLines.length === 0,
    ).length;
    return [
      {
        id: "anchors",
        label: "Âncoras produto/filial",
        value: String(payload.anchors.length),
        hint: "universo completo retornado",
      },
      {
        id: "mod-lines",
        label: "Linhas MOD retornadas",
        value: String(totalLines),
        hint: "soma das operações das âncoras",
      },
      {
        id: "without-lines",
        label: "Âncoras sem linhas",
        value: String(withoutLines),
        hint: "sem operações retornadas no payload",
      },
    ];
  }, [payload]);

  const columns = useMemo<DataTableColumn<BillingModAnchor>[]>(
    () => [
      {
        key: "product",
        header: "Produto",
        render: (row) => (
          <div>
            <div>{row.product}</div>
            {row.productDescription ? (
              <div className="cf-cell-muted">
                {row.productDescription}
              </div>
            ) : null}
          </div>
        ),
      },
      {
        key: "branch",
        header: "Filial",
        render: (row) => row.branch ?? "—",
      },
      {
        key: "billedQty",
        header: "Qtd faturada",
        align: "right",
        render: (row) => fmtNumber(row.billedQty),
      },
      {
        key: "modLines",
        header: "Linhas MOD",
        align: "right",
        render: (row) => String(row.modLines.length),
      },
      {
        key: "situation",
        header: "Situação",
        render: (row) =>
          row.modLines.length > 0 ? (
            <CfStatusBadge label="Com linhas MOD" variant="info" />
          ) : (
            <CfStatusBadge
              label="Sem linhas retornadas"
              variant="warning"
            />
          ),
      },
      {
        key: "detail",
        header: "Detalhe",
        render: (row) => {
          const key = anchorKey(row);
          const active = key === selectedKey;
          return (
            <CfActionButton
              variant={active ? "primary" : "ghost"}
              type="button"
              aria-label={`Ver operações MOD do produto ${row.product}${
                row.branch ? `, filial ${row.branch}` : ""
              }`}
              aria-expanded={active}
              onClick={() =>
                setSelectedKey(active ? null : key)
              }
            >
              {active ? "Ocultar" : "Ver"}
            </CfActionButton>
          );
        },
      },
    ],
    [selectedKey],
  );

  const selectedAnchor =
    payload?.anchors.find((anchor) => anchorKey(anchor) === selectedKey) ??
    null;

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

      <ClosingHero
        title="Faturamento × MOD — R09"
        subtitle={`Competência ${period} · visão operacional · origem Protheus`}
        updatedAt={updatedAt}
        onRefresh={load}
        refreshing={loading && updatedAt !== null}
        metrics={metrics}
        filters={
          <fieldset className="cf-hero-filters">
            <CfSelectField
              label="Filial"
              value={branch}
              options={BRANCH_OPTIONS}
              onChange={(value) => {
                setBranch(value);
                setSelectedKey(null);
              }}
            />
          </fieldset>
        }
        onClearFilters={() => {
          setBranch("all");
          setSelectedKey(null);
        }}
      />

      {loading && !payload ? (
        <p aria-live="polite">Carregando faturamento × MOD…</p>
      ) : state?.kind === "error" ? (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage={`Não foi possível carregar o relatório R09${
            state.error?.message ? ` — ${state.error.message}` : ""
          }.`}
        >
          <CfActionButton
            variant="primary"
            type="button"
            onClick={load}
          >
            Tentar novamente
          </CfActionButton>
        </CfEmptyState>
      ) : payload ? (
        <>
          <DataTableSection<BillingModAnchor>
            title="Produtos faturados"
            titleHint={CF_HELP.billingModBreakdown.table}
            columns={columns}
            rows={payload.anchors}
            rowKey={anchorKey}
            loading={loading}
            emptyMessage="Nenhuma âncora faturada encontrada para a competência/filial selecionadas."
            columnPreferencesKey="cf:closing:billing-mod-breakdown:v1"
          />

          {selectedAnchor ? (
            <AnchorDetail anchor={selectedAnchor} />
          ) : null}

          {payload.parityEvidence ? (
            <details className="cf-disclosure">
              <summary className="cf-disclosure__summary">
                Evidência histórica de paridade — referência{" "}
                {payload.parityEvidence.scope.referencePeriod} (
                {payload.parityEvidence.scope.artifact}) — não comprova a
                competência corrente
              </summary>
              <div className="cf-disclosure__body">
                <p className="cf-muted">
                  {payload.parityEvidence.semantics}
                </p>
                <ul className="cf-muted">
                  <li>
                    Chaves correspondentes:{" "}
                    {payload.parityEvidence.metrics.matchedKeys}/
                    {payload.parityEvidence.metrics.artifactLines} (
                    {payload.parityEvidence.metrics.keyCoveragePct}%)
                  </li>
                  <li>
                    Homologação:{" "}
                    {payload.parityEvidence.scope.homologationStatus}
                  </li>
                  <li>
                    Medido em: {payload.parityEvidence.scope.measuredAt}
                  </li>
                </ul>
              </div>
            </details>
          ) : null}

          {payload.limitations?.length ||
          payload.sourceMissing?.length ? (
            <details className="cf-disclosure">
              <summary className="cf-disclosure__summary">
                Limitações e divergências conhecidas
              </summary>
              <div className="cf-disclosure__body">
                {payload.limitations?.length ? (
                  <ul className="cf-muted">
                    {payload.limitations.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                ) : null}
                {payload.sourceMissing?.length ? (
                  <ul className="cf-muted">
                    {payload.sourceMissing.map((item, index) => (
                      <li key={index}>Fonte ausente: {item}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </details>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

/** Detalhe inline da âncora selecionada — operações MOD completas,
 *  com estados tipados (ausência nunca vira zero). */
function AnchorDetail({ anchor }: { anchor: BillingModAnchor }) {
  const columns = useMemo<DataTableColumn<BillingModLine>[]>(
    () => [
      { key: "level", header: "Nível", render: (row) => row.level },
      {
        key: "product",
        header: "Produto componente",
        render: (row) => (
          <div>
            <div>{row.product ?? "—"}</div>
            {row.productDescription ? (
              <div className="cf-cell-muted">
                {row.productDescription}
              </div>
            ) : null}
          </div>
        ),
      },
      {
        key: "operation",
        header: "Operação",
        render: (row) => (
          <div>
            <div>{row.operation ?? "—"}</div>
            {row.operationDescription ? (
              <div className="cf-cell-muted">
                {row.operationDescription}
              </div>
            ) : null}
          </div>
        ),
      },
      { key: "resource", header: "Recurso", render: (row) => row.resource ?? "—" },
      {
        key: "modItem",
        header: "Item MOD",
        render: (row) => (
          <div>
            <div>{row.modItem ?? "—"}</div>
            {row.modDescription ? (
              <div className="cf-cell-muted">{row.modDescription}</div>
            ) : null}
          </div>
        ),
      },
      { key: "modUnit", header: "Un. MOD", render: (row) => row.modUnit ?? "—" },
      {
        key: "propagatedQty",
        header: "Qtd propagada",
        align: "right",
        render: (row) => fmtNumber(row.propagatedQty),
      },
      {
        key: "stdTime",
        header: "Tempo padrão",
        align: "right",
        render: (row) => fmtTyped(row.stdTime),
      },
      {
        key: "hours",
        header: "Horas",
        align: "right",
        render: (row) => fmtTyped(row.hours),
      },
      {
        key: "costUnit",
        header: "Custo unit.",
        align: "right",
        render: (row) => fmtTyped(row.costUnit),
      },
      {
        key: "costTotal",
        header: "Custo total",
        align: "right",
        render: (row) => fmtTyped(row.costTotal),
      },
      { key: "sourceOp", header: "OP ref.", render: (row) => row.sourceOp ?? "—" },
    ],
    [],
  );

  return (
    <CfSectionCard
      title={`Operações MOD — ${anchor.product}${
        anchor.branch ? ` / Filial ${anchor.branch}` : ""
      }`}
    >
      <p className="cf-muted">
        {anchor.productDescription ? `${anchor.productDescription} · ` : ""}
        Qtd faturada {fmtNumber(anchor.billedQty)} ·{" "}
        {anchor.modLines.length}{" "}
        {anchor.modLines.length === 1
          ? "operação retornada"
          : "operações retornadas"}
        {anchor.sourceMissing?.length
          ? ` · fontes ausentes: ${anchor.sourceMissing.join(", ")}`
          : ""}
      </p>
      {anchor.modLines.length === 0 ? (
        <p className="cf-muted">
          Nenhuma linha MOD retornada para esta âncora no payload da
          competência.
        </p>
      ) : (
        <DataTableSection<BillingModLine>
          title="Operações do roteiro"
          titleHint={CF_HELP.billingModBreakdown.detail}
          columns={columns}
          rows={anchor.modLines}
          rowKey={(row) =>
            `${row.level}|${row.product ?? ""}|${row.operation ?? ""}|${row.resource ?? ""}|${row.modItem ?? ""}`
          }
          hideSearch
          emptyMessage="Nenhuma operação retornada."
        />
      )}
    </CfSectionCard>
  );
}
