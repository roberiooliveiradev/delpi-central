import { Fragment, useEffect, useMemo, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton, SuppliesEmptyState, SuppliesLoadingCard,
  SuppliesPageHero, SuppliesPagePath, SuppliesSectionCard, SuppliesStateBanner,
} from "../../app/suppliesUi";
import {
  getFreightImpact, type FreightDateMode, type FreightFilterSituation,
  type FreightImpactFilters, type FreightImpactInvoice, type FreightImpactResponse,
} from "./api";
import "./FreightImpactPage.css";

function todayLocal(): string {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
function money(value: string | number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return Number(value).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}
function pct(value: string | number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return `${Number(value).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}
function displayDate(value: string): string {
  const [y, m, d] = value.slice(0, 10).split("-");
  return y && m && d ? `${d}/${m}/${y}` : (value || "—");
}
function situationLabel(value: FreightImpactInvoice["situation"]): string {
  if (value === "above_limit") return "Acima da meta";
  if (value === "inconsistent") return "Inconsistente";
  return "Dentro da meta";
}
function invoiceKey(invoice: FreightImpactInvoice): string {
  return [invoice.branch, invoice.invoice_document, invoice.invoice_series, invoice.supplier_code, invoice.supplier_store].join(":");
}

export function FreightImpactPage({ basePath }: { basePath: string }) {
  const session = useSuppliesSession();
  const allowed = useMemo(
    () => session.allowedUnits.filter((code) => code === "01" || code === "02"),
    [session.allowedUnits],
  );
  const allowedKey = allowed.join(",");
  const [branch, setBranch] = useState("all");
  const [dateMode, setDateMode] = useState<FreightDateMode>("issue");
  // Consulta inicial menor para evitar consultas pesadas de histórico no Protheus.
  const [dateFrom, setDateFrom] = useState(() => `${todayLocal().slice(0, 7)}-01`);
  const [dateTo, setDateTo] = useState(todayLocal);
  const [situation, setSituation] = useState<FreightFilterSituation>("all");
  const [applied, setApplied] = useState<FreightImpactFilters | null>(null);
  const [data, setData] = useState<FreightImpactResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [openInvoiceKey, setOpenInvoiceKey] = useState<string | null>(null);

  useEffect(() => {
    if (!allowedKey) return;
    setApplied((current) => current ?? {
      branches: allowedKey.split(","), dateFrom, dateTo, dateMode, situation: "all", page: 1,
    });
    // A primeira consulta usa o filtro inicial; alterações futuras exigem Aplicar filtros.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowedKey]);

  useEffect(() => {
    if (!applied?.branches.length) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getFreightImpact(applied, controller.signal)
      .then((payload) => {
        if (
          payload.source !== "financial_purchase_freight_links"
          || payload.method !== "financial_freight_allocation_v1"
          || !payload.is_complete
        ) {
          throw new Error("A base financeira completa do indicador não pôde ser confirmada.");
        }
        if (!controller.signal.aborted) setData(payload);
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(cause instanceof Error ? cause.message : "Não foi possível consultar os fretes.");
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [applied, refresh]);

  function apply(): void {
    const start = Date.parse(`${dateFrom}T00:00:00Z`);
    const end = Date.parse(`${dateTo}T00:00:00Z`);
    if (
      !dateFrom || !dateTo || !Number.isFinite(start) || !Number.isFinite(end)
      || end < start || end - start > 366 * 86400000 || dateFrom < "2023-01-01"
    ) {
      setError("Informe datas válidas a partir de 2023, com intervalo máximo de 367 dias.");
      return;
    }
    const branches = branch === "all" ? allowed : allowed.filter((code) => code === branch);
    if (!branches.length) {
      setError("Selecione uma unidade à qual você tenha acesso.");
      return;
    }
    setOpenInvoiceKey(null);
    setError(null);
    setApplied({ branches, dateFrom, dateTo, dateMode, situation, page: 1 });
  }

  const summary = data?.summary;
  const maxMonthly = Math.max(1, ...(data?.monthly ?? []).map((month) => Number(month.freight_pct ?? 0)));
  const limits = data?.limits ?? {};

  return <div className="sp-page-stack sp-freight-impact">
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
      current="Frete sobre compras"
    />
    <SuppliesPageHero
      eyebrow="ANÁLISES · COMPRAS COM FRETE VINCULADO"
      title="Frete sobre compras"
      description="Veja quanto do valor das mercadorias corresponde ao frete rateado, com a mesma regra e metas do Portal Financeiro."
    />
    <SuppliesSectionCard title="Filtros" hint="Escolha o mesmo período e a mesma unidade para comparar com o Financeiro.">
      <form className="sp-freight-impact__filters" onSubmit={(event) => { event.preventDefault(); apply(); }}>
        <label>Unidade
          <select aria-label="Unidade" value={branch} onChange={(event) => setBranch(event.target.value)}>
            <option value="all">Todas as unidades autorizadas</option>
            {allowed.map((code) => (
              <option key={code} value={code}>{code === "01" ? "01 · Matriz SC" : "02 · Filial ES"}</option>
            ))}
          </select>
        </label>
        <label>Consultar por
          <select aria-label="Consultar por" value={dateMode} onChange={(event) => setDateMode(event.target.value as FreightDateMode)}>
            <option value="issue">Data de emissão da nota</option>
            <option value="entry">Data de digitação da nota</option>
          </select>
        </label>
        <label>Data inicial
          <input aria-label="Data inicial" type="date" required min="2023-01-01"
            value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
        </label>
        <label>Data final
          <input aria-label="Data final" type="date" required min="2023-01-01"
            value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        </label>
        <label>Situação
          <select aria-label="Situação" value={situation} onChange={(event) => setSituation(event.target.value as FreightFilterSituation)}>
            <option value="all">Todas as situações</option>
            <option value="normal">Dentro da meta</option>
            <option value="above_limit">Acima da meta</option>
            <option value="inconsistent">Inconsistente</option>
          </select>
        </label>
        <div className="sp-freight-impact__actions">
          <SuppliesActionButton type="submit" variant="primary" disabled={loading || !allowed.length}>Aplicar filtros</SuppliesActionButton>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !applied}
            onClick={() => setRefresh((value) => value + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </SuppliesActionButton>
        </div>
      </form>
    </SuppliesSectionCard>
    {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
    {!allowed.length ? <SuppliesEmptyState title="Sem unidades autorizadas" message="Solicite o acesso necessário ao Portal Suprimentos." /> : null}
    {loading ? <SuppliesLoadingCard title="Conferindo fretes e notas no Protheus" variant="panel" /> : null}

    {!loading && data && summary ? <>
      <div className="sp-freight-impact__meta" role="note">
        <strong>Metas do Financeiro:</strong>
        {Object.entries(limits).map(([code, limit]) => (
          <span key={code}>{code === "01" ? "Matriz SC" : "Filial ES"} · {pct(limit)}</span>
        ))}
        <small>Uma nota fica acima da meta somente quando o percentual supera o limite da própria filial.</small>
      </div>
      <div className="sp-freight-impact__metrics" aria-label="Resumo dos fretes">
        {[
          { label: "% frete do período", value: pct(summary.freight_pct) },
          { label: "Mercadorias das notas vinculadas", value: money(summary.purchases_total) },
          { label: "Frete rateado", value: money(summary.freight_total) },
          { label: "Notas consideradas", value: summary.invoice_count.toLocaleString("pt-BR") },
          { label: "Acima da meta", value: summary.above_limit_count.toLocaleString("pt-BR"), alert: summary.above_limit_count > 0 },
          { label: "Notas inconsistentes", value: summary.inconsistent_count.toLocaleString("pt-BR") },
        ].map((metric) => (
          <div key={metric.label} className={`sp-freight-impact__metric${metric.alert ? " sp-freight-impact__metric--alert" : ""}`}>
            <span>{metric.label}</span><strong>{metric.value}</strong>
          </div>
        ))}
      </div>
      <p className="sp-freight-impact__scope" role="note">
        Os totais seguem o Financeiro: consideram notas com frete vinculado e dados consistentes.
        Notas sem vínculo não aparecem nesta análise; notas inconsistentes aparecem na lista, mas não entram no percentual.
        O filtro Situação altera a lista, não os totais.
      </p>
      <SuppliesSectionCard title="Evolução mensal" hint="Valores agrupados pelo mês de emissão da nota. O percentual usa a soma das mercadorias e dos fretes rateados, não a média das notas.">
        {data.monthly.length === 0
          ? <SuppliesEmptyState title="Sem movimento" message="Nenhuma nota com frete válido neste período." />
          : <div className="sp-freight-impact__chart" role="img" aria-label="Evolução mensal do percentual de frete">
            {data.monthly.map((month) => (
              <div key={month.period} className="sp-freight-impact__month"
                title={`${month.period}: ${money(month.freight_cost)} / ${money(month.purchase_cost)}`}>
                <div className="sp-freight-impact__month-graphic">
                  <div className="sp-freight-impact__bar"
                    style={{ height: `${Math.max(2, 145 * Number(month.freight_pct ?? 0) / maxMonthly)}px` }} />
                </div>
                <strong>{pct(month.freight_pct)}</strong>
                <span>{month.period.slice(5)}/{month.period.slice(0, 4)}</span>
              </div>
            ))}
          </div>}
      </SuppliesSectionCard>
      <SuppliesSectionCard title="Frete por nota fiscal" hint="Clique em Ver rateio para conferir os documentos de transporte, as parcelas do frete e a base de divisão.">
        {data.items.length === 0
          ? <SuppliesEmptyState title="Nenhuma nota nesta situação" message="Ajuste o período, unidade ou filtro de situação." />
          : <div className="sp-freight-impact__table-wrap">
            <table className="sp-freight-impact__table">
              <thead><tr>
                <th>Filial</th><th>NF / série</th><th>Fornecedor</th><th>Emissão</th>
                <th>Mercadorias</th><th>Frete rateado</th><th>% frete</th><th>Meta</th>
                <th>Situação</th><th>CT-es</th><th>Detalhes</th>
              </tr></thead>
              <tbody>
                {data.items.map((item) => {
                  const key = invoiceKey(item);
                  const isOpen = key === openInvoiceKey;
                  return <Fragment key={key}>
                    <tr className={`sp-freight-impact__row--${item.situation}`}>
                      <td>{item.branch}</td>
                      <td>{item.invoice_document} / {item.invoice_series}</td>
                      <td>{item.supplier_name || `${item.supplier_code}/${item.supplier_store}`}</td>
                      <td>{displayDate(item.issue_date)}</td>
                      <td className="sp-freight-impact__numeric">{money(item.goods_value)}</td>
                      <td className="sp-freight-impact__numeric">{money(item.freight_total)}</td>
                      <td className={`sp-freight-impact__numeric${item.situation === "above_limit" ? " sp-freight-impact__over-limit" : ""}`}>
                        {pct(item.freight_pct)}
                      </td>
                      <td className="sp-freight-impact__numeric">{pct(item.freight_limit)}</td>
                      <td><span className={`sp-freight-impact__status sp-freight-impact__status--${item.situation}`}>
                        {item.situation === "above_limit" ? <AlertTriangle size={13} aria-hidden="true" /> : null}
                        {situationLabel(item.situation)}
                      </span></td>
                      <td className="sp-freight-impact__numeric">{item.cte_count}</td>
                      <td>
                        <button type="button" className="sp-freight-impact__detail-toggle"
                          aria-expanded={isOpen}
                          onClick={() => setOpenInvoiceKey(isOpen ? null : key)}>
                          {isOpen ? <ChevronUp size={15} aria-hidden="true" /> : <ChevronDown size={15} aria-hidden="true" />}
                          {isOpen ? "Recolher" : "Ver rateio"}
                        </button>
                      </td>
                    </tr>
                    {isOpen ? <tr className="sp-freight-impact__detail-row">
                      <td colSpan={11}>
                        <div className="sp-freight-impact__detail">
                          <div className="sp-freight-impact__detail-heading">
                            <strong>Composição do frete · NF {item.invoice_document}/{item.invoice_series}</strong>
                            <span>{item.supplier_name} ({item.supplier_code}/{item.supplier_store})</span>
                          </div>
                          <div className="sp-freight-impact__detail-facts">
                            <span>Emissão: <strong>{displayDate(item.issue_date)}</strong></span>
                            <span>Digitação: <strong>{displayDate(item.entry_date)}</strong></span>
                            <span>Mercadorias: <strong>{money(item.goods_value)}</strong></span>
                            <span>Frete rateado: <strong>{money(item.freight_total)}</strong></span>
                            <span>Percentual: <strong>{pct(item.freight_pct)}</strong></span>
                            <span>Meta da filial: <strong>{pct(item.freight_limit)}</strong></span>
                          </div>
                          {item.reason_codes.length > 0 ? <p className="sp-freight-impact__issues">
                            <strong>Conferir no Protheus: </strong>
                            {item.reason_codes.map((reason) => data.reason_labels[reason] ?? reason).join("; ")}
                          </p> : null}
                          <div className="sp-freight-impact__table-wrap">
                            <table className="sp-freight-impact__allocation-table">
                              <thead><tr>
                                <th>CT-e / série</th><th>Transportadora</th><th>Emissão do CT-e</th>
                                <th>Valor bruto CT-e</th><th>Base do rateio</th><th>NFs no CT-e</th><th>Parcela desta nota</th>
                              </tr></thead>
                              <tbody>
                                {item.allocations.map((allocation) => (
                                  <tr key={`${allocation.freight_document}:${allocation.freight_series}:${allocation.carrier_code}:${allocation.carrier_store}`}>
                                    <td>
                                      <strong>{allocation.freight_document}/{allocation.freight_series}</strong>
                                      {allocation.freight_access_key
                                        ? <small title={allocation.freight_access_key}>Chave: {allocation.freight_access_key}</small>
                                        : null}
                                    </td>
                                    <td>{allocation.carrier_name || `${allocation.carrier_code}/${allocation.carrier_store}`}</td>
                                    <td>{displayDate(allocation.freight_issue_date)}</td>
                                    <td className="sp-freight-impact__numeric">{money(allocation.freight_gross_value)}</td>
                                    <td className="sp-freight-impact__numeric">{money(allocation.allocation_base)}</td>
                                    <td className="sp-freight-impact__numeric">{allocation.linked_invoice_count}</td>
                                    <td className="sp-freight-impact__numeric"><strong>{money(allocation.allocated_value)}</strong></td>
                                  </tr>
                                ))}
                                {!item.allocations.length ? <tr><td colSpan={7}>Nenhum rateio válido encontrado para esta nota.</td></tr> : null}
                              </tbody>
                            </table>
                          </div>
                          <p className="sp-freight-impact__allocation-note">
                            Quando um CT-e atende várias notas, o valor bruto é dividido proporcionalmente
                            ao valor das mercadorias de cada uma. A base pode incluir notas fora do filtro atual.
                          </p>
                        </div>
                      </td>
                    </tr> : null}
                  </Fragment>;
                })}
              </tbody>
            </table>
          </div>}
        <div className="sp-freight-impact__pager">
          <span>Página {data.page} de {data.total_pages} · {data.total.toLocaleString("pt-BR")} notas na situação selecionada</span>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !applied || data.page <= 1}
            onClick={() => { if (applied) { setOpenInvoiceKey(null); setApplied({ ...applied, page: applied.page - 1 }); } }}>
            Anterior
          </SuppliesActionButton>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !applied || data.page >= data.total_pages}
            onClick={() => { if (applied) { setOpenInvoiceKey(null); setApplied({ ...applied, page: applied.page + 1 }); } }}>
            Próxima
          </SuppliesActionButton>
        </div>
      </SuppliesSectionCard>
      <SuppliesSectionCard title="Como funciona o cálculo?" collapsible defaultOpen={false}>
        <div className="sp-freight-impact__help">
          <p><strong>Valor das mercadorias:</strong> registrado na nota de compra no Protheus. Não é a soma dos custos dos itens usada na versão anterior.</p>
          <p><strong>Frete rateado:</strong> o valor bruto de cada CT-e é dividido proporcionalmente entre todas as notas que ele atende. O ajuste de centavos garante que a soma das parcelas corresponda ao CT-e.</p>
          <p><strong>% da nota:</strong> frete rateado ÷ valor das mercadorias × 100. Quando ultrapassa {pct(limits["01"])} na matriz ou {pct(limits["02"])} na filial ES, a linha fica vermelha.</p>
          <p><strong>Inconsistências:</strong> vínculos sem documento, valores inválidos ou outros problemas aparecem para conferência, mas não são somados ao percentual geral.</p>
          <p><strong>Base analisada:</strong> apenas notas com vínculo de frete. Para comparar com o Portal Financeiro, use a mesma unidade e o mesmo tipo de data.</p>
        </div>
      </SuppliesSectionCard>
    </> : null}
  </div>;
}
