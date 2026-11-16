import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
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
  const [dateFrom, setDateFrom] = useState(() => todayLocal().slice(0, 4) + "-01-01");
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
        if (payload.scope !== "confirmed_release_to_first_order" ||
            payload.period_anchor !== "final_approval_date" ||
            payload.source !== "SC1010+SCR010+SC7010") {
          throw new Error("A origem comprovada do indicador não foi confirmada.");
        }
        setData(payload);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Falha na consulta.");
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
    { label: "Tempo médio até o 1º PC", value: summary?.avg_days == null ? "—" : formatNumber(summary.avg_days, 2) + " dias" },
    { label: "SCs convertidas", value: formatNumber(summary?.converted_requests) },
    { label: "Ainda sem PC", value: formatNumber(summary?.pending_requests) },
    { label: "PC antes da liberação", value: formatNumber(summary?.before_release) },
    { label: "PC com dado inválido", value: formatNumber(summary?.invalid_order_dates) },
  ];
  const buckets = [
    { label: "Mesmo dia", count: summary?.same_day ?? 0 },
    { label: "1 a 2 dias", count: summary?.one_to_two_days ?? 0 },
    { label: "3 a 5 dias", count: summary?.three_to_five_days ?? 0 },
    { label: "6 a 10 dias", count: summary?.six_to_ten_days ?? 0 },
    { label: "Acima de 10 dias", count: summary?.over_ten_days ?? 0 },
  ];
  const eligible = Math.max(summary?.converted_requests ?? 0, 1);

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
        description="Da última aprovação válida na alçada até a emissão do primeiro pedido vinculado. Uma SC conta uma vez na média."
      />
      <SuppliesSectionCard
        title="Filtros do indicador"
        hint="Competência pela data da última liberação da alçada. Dias corridos."
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
            Liberação de
            <input aria-label="Liberação de" type="date" required value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </label>
          <label>
            Liberação até
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
          <section className="sp-approval-lead-time__metrics" aria-label="Resumo da conversão">
            {metrics.map((metric) => (
              <div key={metric.label} className="sp-approval-lead-time__metric">
                <span>{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </section>
          <SuppliesSectionCard title="Distribuição do prazo de conversão" hint="Somente SCs convertidas com liberação e PC válidos">
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
                      <th>SC</th><th>Unidade</th><th>Última liberação</th>
                      <th>Primeiro PC</th><th>Emissão PC</th><th>PCs vinculados</th>
                      <th>Situação</th><th>Tempo</th>
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
                        <td>{formatDate(item.final_approval_date)}</td>
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
                        <td><strong>{item.conversion_days == null ? "—" : formatNumber(item.conversion_days) + " d"}</strong></td>
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
            Fonte: SCR010 (liberação comprovada), SC1010 (SC) e SC7010 (PC vinculado).
            SC sem PC fica pendente; PC anterior à liberação e dados inválidos não entram na média.
            Os prazos são dias corridos. Aprovações retroativas e reaprovações devem ser conferidas
            com Compras. O primeiro PC indica início de conversão, não atendimento total da SC.
          </p>
        </>
      ) : null}
    </div>
  );
}
