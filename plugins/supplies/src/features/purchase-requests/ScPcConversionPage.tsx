import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { ApiRequestError } from "../../api/httpClient";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import { buildPurchaseOrderDetailPath, buildPurchaseRequestDetailPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton, SuppliesEmptyState, SuppliesLoadingCard,
  SuppliesPageHero, SuppliesPagePath, SuppliesSectionCard, SuppliesStateBanner,
} from "../../app/suppliesUi";
import {
  getScPcConversion, type ScPcConversionFilters, type ScPcConversionResponse,
  type ScPcConversionStatus,
} from "./scPcConversionApi";
import "./ApprovalLeadTimePage.css";

function todayLocal() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  const [y, m, d] = value.slice(0, 10).split("-");
  return y && m && d ? [d, m, y].join("/") : value;
}

const labels: Record<ScPcConversionStatus, string> = {
  converted: "Convertida",
  pending: "Aguardando PC",
  order_before_release: "PC anterior à liberação",
  invalid_order_date: "Data/identidade do PC inválida",
};

const formatNumber = (n: number | null | undefined, digits = 0) =>
  n == null ? "—" : n.toLocaleString("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export function ScPcConversionPage({ basePath }: { basePath: string }) {
  const session = useSuppliesSession();
  const units = useMemo(
    () => session.allowedUnits.filter((unit) => unit === "01" || unit === "02"),
    [session.allowedUnits],
  );
  const [branch, setBranch] = useState("all");
  const [dateFrom, setDateFrom] = useState(() => todayLocal().slice(0, 7) + "-01");
  const [dateTo, setDateTo] = useState(todayLocal);
  const [requestNumber, setRequestNumber] = useState("");
  const [applied, setApplied] = useState<ScPcConversionFilters | null>(null);
  const [data, setData] = useState<ScPcConversionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  const unitKey = units.join(",");
  useEffect(() => {
    if (!unitKey) return;
    setApplied((previous) => previous ?? {
      branches: unitKey.split(","), dateFrom, dateTo,
      requestNumber: "", page: 1,
    });
  }, [unitKey, dateFrom, dateTo]);

  useEffect(() => {
    if (!applied?.branches.length) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getScPcConversion(applied, controller.signal)
      .then((payload) => {
        if (payload.scope !== "release_or_issue_without_approval_to_first_order" ||
            payload.period_anchor !== "effective_start_date" ||
            payload.source !== "SC1010+SCR010+SC7010" ||
            payload.calculation_mode !== "completed_or_pending_elapsed_as_of_today" ||
            !payload.as_of_date) {
          throw new Error("A origem comprovada do indicador não foi confirmada.");
        }
        setData(payload);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        if (err instanceof ApiRequestError && err.code === "upstream_timeout") {
          setError("O Protheus demorou mais que o limite da consulta. Tente um período menor ou outra unidade.");
        } else if (err instanceof ApiRequestError && err.code === "totvs_unavailable") {
          setError("A consulta ao Protheus está indisponível. Verifique o serviço de dados e tente novamente.");
        } else if (err instanceof ApiRequestError && err.code === "upstream_failure") {
          setError("Falha na API de dados do indicador. A equipe de TI pode conferir o log da api-delpi.");
        } else {
          setError(err instanceof Error ? err.message : "Falha na consulta.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [applied, reload]);

  const apply = () => {
    if (!units.length) return;
    const start = new Date(dateFrom + "T00:00:00");
    const end = new Date(dateTo + "T00:00:00");
    const span = Math.round((end.getTime() - start.getTime()) / 86400000);
    if (!dateFrom || !dateTo || !Number.isFinite(span) || span < 0 || span > 366) {
      setError("O período deve conter até 367 dias, com início anterior ao fim.");
      return;
    }
    if (requestNumber.trim() && !/^\d{1,16}$/.test(requestNumber.trim())) {
      setError("Informe somente os dígitos da SC.");
      return;
    }
    setError(null);
    setApplied({
      branches: branch === "all" ? units : units.filter((unit) => unit === branch),
      dateFrom, dateTo, requestNumber, page: 1,
    });
  };

  const summary = data?.summary;
  const changePage = (page: number) => {
    if (!applied || !data || loading || page < 1 || page > data.total_pages) return;
    setApplied({ ...applied, page });
  };

  const metrics = [
    { label: "SCs liberadas (amostra)", value: formatNumber(summary?.approved_requests) },
    { label: "Com alçada de compras", value: formatNumber(summary?.with_approval) },
    { label: "Sem alçada (emissão SC)", value: formatNumber(summary?.without_approval) },
    { label: "Média atual · incluindo pendentes", value: summary?.avg_days == null ? "—" : formatNumber(summary.avg_days, 2) + " dias" },
    { label: "Média das SCs convertidas", value: summary?.avg_completed_days == null ? "—" : formatNumber(summary.avg_completed_days, 2) + " dias" },
    { label: "Idade média das SCs sem PC", value: summary?.avg_pending_days == null ? "—" : formatNumber(summary.avg_pending_days, 2) + " dias" },
    { label: "SCs convertidas", value: formatNumber(summary?.converted_requests) },
    { label: "Ainda sem PC", value: formatNumber(summary?.pending_requests) },
    { label: "PC anterior ao início", value: formatNumber(summary?.before_release) },
    { label: "PC com dado inválido", value: formatNumber(summary?.invalid_order_dates) },
  ];
  const buckets = [
    { label: "Mesmo dia", count: summary?.same_day ?? 0 },
    { label: "1 a 2 dias", count: summary?.one_to_two_days ?? 0 },
    { label: "3 a 5 dias", count: summary?.three_to_five_days ?? 0 },
    { label: "6 a 10 dias", count: summary?.six_to_ten_days ?? 0 },
    { label: "Acima de 10 dias", count: summary?.over_ten_days ?? 0 },
  ];
  const eligible = Math.max(summary?.measured_requests ?? 0, 1);

  return (
    <div className="sp-page-stack sp-approval-lead-time">
      <SuppliesPagePath
        back={{
          label: "Solicitações",
          href: basePath + "/purchase-requests",
          onNavigate: (event) => { event.preventDefault(); navigatePluginView("purchase_requests", { basePath }); },
        }}
        items={[]}
        current="Conversão SC → PC"
      />
      <SuppliesPageHero
        eyebrow="Portal Suprimentos / Eficiência de Compras"
        title="Tempo de conversão SC → PC"
        description="Da liberação da alçada ou emissão da SC sem alçada até o primeiro PC. SCs ainda sem pedido continuam contando dias até hoje e entram na média."
      />
      <SuppliesSectionCard
        title="Filtros do indicador"
        hint="Competência pelo início da contagem: liberação da alçada ou emissão da SC sem alçada. Dias corridos."
      >
        <form className="sp-approval-lead-time__filters" onSubmit={(event) => { event.preventDefault(); apply(); }}>
          <label>
            Unidade
            <select aria-label="Unidade" value={branch} onChange={(event) => setBranch(event.target.value)}>
              <option value="all">Todas as unidades autorizadas</option>
              {units.map((unit) => (
                <option key={unit} value={unit}>{unit === "01" ? "01 · Matriz SC" : "02 · Filial ES"}</option>
              ))}
            </select>
          </label>
          <label>
            Início da contagem de
            <input aria-label="Liberação de" type="date" required value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </label>
          <label>
            Início da contagem até
            <input aria-label="Liberação até" type="date" required value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </label>
          <label>
            Número da SC
            <input aria-label="Número da SC" inputMode="numeric" placeholder="Opcional" value={requestNumber} onChange={(event) => setRequestNumber(event.target.value)} />
          </label>
          <SuppliesActionButton type="submit" variant="primary" disabled={loading || !units.length}>Aplicar</SuppliesActionButton>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !units.length} onClick={() => setReload((count) => count + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </SuppliesActionButton>
        </form>
      </SuppliesSectionCard>
      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!units.length ? <SuppliesEmptyState title="Sem unidades disponíveis" message="É necessário ter acesso ao Portal Suprimentos." /> : null}
      {loading ? <SuppliesLoadingCard title="Consultando eventos de aprovação e pedidos no Protheus" variant="panel" /> : null}
      {!loading && data ? (
        <>
          <p className="sp-approval-lead-time__note">
            <strong>Referência das pendências: {formatDate(data.as_of_date)}.</strong>{" "}
            O tempo das SCs sem PC aumenta a cada dia. A média principal considera
            tanto as convertidas quanto as pendentes, com uma SC por observação.
          </p>
          <section className="sp-approval-lead-time__metrics" aria-label="Resumo da conversão">
            {metrics.map((metric) => (
              <div key={metric.label} className="sp-approval-lead-time__metric">
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </section>
          <SuppliesSectionCard title="Distribuição do tempo transcorrido" hint="SCs com PC: início até a emissão. SCs sem PC: início até hoje. Anomalias não entram.">
            <div className="sp-approval-lead-time__buckets">
              {buckets.map((bucket) => (
                <div key={bucket.label}>
                  <div className="sp-approval-lead-time__bucket-label">
                    <span>{bucket.label}</span>
                    <strong>{formatNumber(bucket.count)} · {formatNumber(100 * bucket.count / eligible, 1)}%</strong>
                  </div>
                  <div className="sp-approval-lead-time__bar">
                    <div style={{ width: String(100 * bucket.count / eligible) + "%" }} />
                  </div>
                </div>
              ))}
            </div>
          </SuppliesSectionCard>
          <SuppliesSectionCard title="Solicitações e seus primeiros pedidos" hint="Abra as fichas de SC/PC para investigar cada conversão">
            {!data.items.length ? (
              <SuppliesEmptyState title="Nenhuma SC liberada no período" message="Altere a competência ou a unidade para ampliar a consulta." />
            ) : (
              <div className="sp-approval-lead-time__table-scroll">
                <table className="sp-approval-lead-time__table">
                  <thead>
                    <tr>
                      <th>SC</th><th>Unidade</th><th>Início da contagem</th>
                      <th>Primeiro PC</th><th>Emissão PC</th><th>PCs vinculados</th>
                      <th>Situação</th><th>Tempo transcorrido</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((item) => (
                      <tr key={item.branch + ":" + item.request_number}>
                        <td>
                          <button type="button" className="sp-approval-lead-time__link"
                            onClick={() => navigatePluginPath(buildPurchaseRequestDetailPath(item.branch, item.request_number, basePath))}>
                            {item.request_number}
                          </button>
                        </td>
                        <td>{item.branch}</td>
                        <td>
                          <strong>{formatDate(item.effective_start_date)}</strong>
                          <div className="sp-approval-lead-time__note">
                            {item.start_date_source === "approval_release" ? "Liberação da alçada" : "Emissão SC · sem alçada"}
                          </div>
                        </td>
                        <td>
                          {item.first_order_number ? (
                            <button type="button" className="sp-approval-lead-time__link"
                              onClick={() => navigatePluginPath(buildPurchaseOrderDetailPath(item.branch, item.first_order_number!, basePath))}>
                              {item.first_order_number}
                            </button>
                          ) : "—"}
                        </td>
                        <td>{formatDate(item.first_order_date)}</td>
                        <td>{formatNumber(item.linked_order_count)}</td>
                        <td>{labels[item.conversion_status]}</td>
                        <td>
                          <strong>{item.conversion_days == null ? "—" : formatNumber(item.conversion_days) + " d"}</strong>
                          {item.conversion_status === "pending" && item.pending_age_days != null ? (
                            <div className="sp-approval-lead-time__note">até {formatDate(data.as_of_date)}</div>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="sp-approval-lead-time__footer">
              <span>{formatNumber(data.total)} SCs liberadas · página {data.page} de {Math.max(data.total_pages, 1)}</span>
              <div>
                <SuppliesActionButton type="button" variant="ghost" disabled={data.page <= 1} onClick={() => changePage(data.page - 1)}>Anterior</SuppliesActionButton>
                <SuppliesActionButton type="button" variant="ghost" disabled={data.page >= data.total_pages} onClick={() => changePage(data.page + 1)}>Próxima</SuppliesActionButton>
              </div>
            </div>
          </SuppliesSectionCard>
          <p className="sp-approval-lead-time__note">
            Fonte: SCR010 (alçada existente), SC1010 (SC sem alçada) e SC7010 (PC vinculado).
            A emissão da SC somente inicia o prazo quando não houver nenhum histórico SCR e todos os itens estiverem liberados.
            SC sem PC fica pendente, mas seus dias até a data de referência entram na média.
            Apenas inconsistências (PC anterior à data inicial, dados inválidos ou início futuro)
            ficam fora. Os prazos são dias corridos. Aprovações retroativas e reaprovações devem ser conferidas
            com Compras. O primeiro PC indica início de conversão, não atendimento total da SC.
          </p>
        </>
      ) : null}
    </div>
  );
}
