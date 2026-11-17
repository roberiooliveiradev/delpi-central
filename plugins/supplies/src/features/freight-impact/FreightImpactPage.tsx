import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton, SuppliesEmptyState, SuppliesLoadingCard,
  SuppliesPageHero, SuppliesPagePath, SuppliesSectionCard, SuppliesStateBanner,
} from "../../app/suppliesUi";
import { getFreightImpact, type FreightImpactFilters, type FreightImpactResponse } from "./api";
import "./FreightImpactPage.css";

function todayLocal(): string {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
function money(value: number | null | undefined): string {
  return value == null ? "—" : value.toLocaleString("pt-BR", {style:"currency",currency:"BRL"});
}
function pct(value: number | null | undefined): string {
  return value == null ? "—" : `${value.toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2})}%`;
}
function displayDate(value: string): string {
  const [y,m,d] = value.slice(0,10).split("-");
  return y && m && d ? `${d}/${m}/${y}` : value;
}
export function FreightImpactPage({basePath}:{basePath:string}) {
  const session = useSuppliesSession();
  const allowed = useMemo(() => session.allowedUnits.filter(code => code === "01" || code === "02"), [session.allowedUnits]);
  const allowedKey = allowed.join(",");
  const [branch,setBranch] = useState("all");
  const [dateFrom,setDateFrom] = useState(() => `${todayLocal().slice(0,4)}-01-01`);
  const [dateTo,setDateTo] = useState(todayLocal);
  const [applied,setApplied] = useState<FreightImpactFilters | null>(null);
  const [data,setData] = useState<FreightImpactResponse | null>(null);
  const [loading,setLoading] = useState(false);
  const [error,setError] = useState<string | null>(null);
  const [refresh,setRefresh] = useState(0);

  useEffect(() => {
    if (!allowedKey) return;
    setApplied(current => current ?? {branches:allowedKey.split(","),dateFrom,dateTo,page:1});
  },[allowedKey,dateFrom,dateTo]);
  useEffect(() => {
    if (!applied?.branches.length) return;
    const controller = new AbortController();
    setLoading(true); setError(null);
    getFreightImpact(applied,controller.signal)
      .then(payload => {
        if (payload.source !== "SF1010+SD1010+SF8010" || payload.method !== "DLP02R01_cost") {
          throw new Error("A fonte oficial do indicador não foi confirmada.");
        }
        if (!controller.signal.aborted) setData(payload);
      })
      .catch((cause:unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(cause instanceof Error ? cause.message : "Falha ao consultar o Protheus.");
      })
      .finally(() => {if (!controller.signal.aborted) setLoading(false);});
    return () => controller.abort();
  },[applied,refresh]);

  function apply(): void {
    const start = Date.parse(`${dateFrom}T00:00:00Z`);
    const end = Date.parse(`${dateTo}T00:00:00Z`);
    if (!dateFrom || !dateTo || !Number.isFinite(start) || !Number.isFinite(end)
        || end < start || end - start > 366 * 86400000 || dateFrom < "2023-01-01") {
      setError("Informe datas válidas a partir de 2023, com intervalo máximo de 367 dias.");
      return;
    }
    const branches = branch === "all" ? allowed : allowed.filter(code => code === branch);
    if (!branches.length) {setError("Selecione uma filial autorizada.");return;}
    setError(null);
    setApplied({branches,dateFrom,dateTo,page:1});
  }
  const summary = data?.summary;
  const maxMonthly = Math.max(1,...(data?.monthly ?? []).map(x => x.freight_pct ?? 0));
  return <div className="sp-page-stack sp-freight-impact">
    <SuppliesPagePath back={{label:"Visão geral",href:buildPluginPath("overview",basePath),onNavigate:event => {
      event.preventDefault();navigatePluginView("overview",{basePath});
    }}} items={[]} current="Frete sobre compras"/>
    <SuppliesPageHero eyebrow="ANÁLISES · COMPRAS NACIONAIS" title="Frete sobre compras"
      description="Quanto o transporte representa do custo das compras nacionais. Base fiscal Protheus DLP02R01."/>
    <SuppliesSectionCard title="Filtros" hint="Período pela emissão da NF de compra.">
      <form className="sp-freight-impact__filters" onSubmit={event => {event.preventDefault();apply();}}>
        <label>Unidade<select aria-label="Unidade" value={branch} onChange={event => setBranch(event.target.value)}>
          <option value="all">Todas as unidades autorizadas</option>
          {allowed.map(code => <option key={code} value={code}>{code === "01" ? "01 · Matriz SC" : "02 · Filial ES"}</option>)}
        </select></label>
        <label>Emissão inicial<input aria-label="Emissão inicial" type="date" min="2023-01-01" required value={dateFrom} onChange={event => setDateFrom(event.target.value)}/></label>
        <label>Emissão final<input aria-label="Emissão final" type="date" min="2023-01-01" required value={dateTo} onChange={event => setDateTo(event.target.value)}/></label>
        <div className="sp-freight-impact__actions">
          <SuppliesActionButton type="submit" variant="primary" disabled={loading || !allowed.length}>Aplicar filtros</SuppliesActionButton>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !applied} onClick={() => setRefresh(value => value+1)}>
            <RefreshCw size={16} aria-hidden="true"/>Atualizar
          </SuppliesActionButton>
        </div>
      </form>
    </SuppliesSectionCard>
    {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
    {!allowed.length ? <SuppliesEmptyState title="Sem filiais autorizadas" message="É necessário ter acesso às unidades de Suprimentos."/> : null}
    {loading ? <SuppliesLoadingCard title="Consultando notas e CT-es no Protheus" variant="panel"/> : null}
    {!loading && data && summary ? <>
      {summary.invalid_base_count > 0 ? <SuppliesStateBanner>{summary.invalid_base_count} NF(s) sem custo de mercadoria positivo, exibidas mas fora da base percentual.</SuppliesStateBanner> : null}
      <div className="sp-freight-impact__metrics" aria-label="Resumo do frete">
        {[
          {label:"Frete sobre compras",value:pct(summary.freight_pct)},
          {label:"Compras nacionais",value:money(summary.purchases_total)},
          {label:"Frete nacional vinculado",value:money(summary.freight_total)},
          {label:"Notas analisadas",value:summary.invoice_count.toLocaleString("pt-BR")},
          {label:"NFs sem frete vinculado",value:summary.without_freight_count.toLocaleString("pt-BR")},
        ].map(metric => <div key={metric.label} className="sp-freight-impact__metric"><span>{metric.label}</span><strong>{metric.value}</strong></div>)}
      </div>
      <SuppliesSectionCard title="Evolução mensal" hint="Frete dividido pela base de compras do mês, não média de percentuais por nota.">
        {data.monthly.length === 0 ? <SuppliesEmptyState title="Sem movimento" message="Nenhuma nota encontrada no período."/> :
          <div className="sp-freight-impact__chart" role="img" aria-label="Evolução mensal do percentual de frete">
            {data.monthly.map(month => <div key={month.period} className="sp-freight-impact__month" title={`${month.period}: ${money(month.freight_cost)} / ${money(month.purchase_cost)}`}>
              <div className="sp-freight-impact__month-graphic"><div className="sp-freight-impact__bar" style={{height:`${Math.max(2,145*(month.freight_pct ?? 0)/maxMonthly)}px`}}/></div>
              <strong>{pct(month.freight_pct)}</strong><span>{month.period.slice(5)}/{month.period.slice(0,4)}</span>
            </div>)}
          </div>}
      </SuppliesSectionCard>
      <SuppliesSectionCard title="Frete por nota fiscal" hint="Uma linha por filial, NF, série e fornecedor; custos em D1_CUSTO.">
        {data.items.length === 0 ? <SuppliesEmptyState title="Nenhuma NF" message="Sem compras nacionais neste filtro."/> :
          <div className="sp-freight-impact__table-wrap"><table className="sp-freight-impact__table">
            <thead><tr><th>Filial</th><th>NF / série</th><th>Fornecedor</th><th>Emissão</th><th>Compras (R$)</th><th>Frete (R$)</th><th>% frete</th><th>CT-es</th></tr></thead>
            <tbody>{data.items.map(item => <tr key={`${item.branch}:${item.invoice_document}:${item.invoice_series}:${item.supplier_code}:${item.supplier_store}`}>
              <td>{item.branch}</td><td>{item.invoice_document} / {item.invoice_series}</td>
              <td>{item.supplier_name || `${item.supplier_code}/${item.supplier_store}`}</td>
              <td>{displayDate(item.issue_date)}</td><td>{money(item.purchase_cost)}</td><td>{money(item.freight_cost)}</td>
              <td>{pct(item.freight_pct)}</td><td>{item.cte_count}</td>
            </tr>)}</tbody>
          </table></div>}
        <div className="sp-freight-impact__pager">
          <span>Página {data.page} de {Math.max(1,data.total_pages)} · {data.total.toLocaleString("pt-BR")} notas</span>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !applied || data.page <= 1}
            onClick={() => {if (applied) setApplied({...applied,page:applied.page-1});}}>Anterior</SuppliesActionButton>
          <SuppliesActionButton type="button" variant="ghost" disabled={loading || !applied || data.page >= data.total_pages}
            onClick={() => {if (applied) setApplied({...applied,page:applied.page+1});}}>Próxima</SuppliesActionButton>
        </div>
      </SuppliesSectionCard>
      <SuppliesSectionCard title="Critérios do indicador" collapsible defaultOpen={false}>
        <div className="sp-freight-impact__help">
          <p><strong>Fórmula:</strong> soma dos custos de frete dos CT-es vinculados ÷ soma dos custos de todas as NFs nacionais elegíveis × 100. Sem média simples.</p>
          <p><strong>Origem:</strong> SF1, SD1 e SF8, referência DLP02R01. Valores D1_CUSTO, não valor bruto da NF. Data de emissão da NF define o período.</p>
          <p><strong>Compras nacionais:</strong> entradas normais NF-e (SPED) de fornecedores com UF brasileira cadastrada. As NFs sem frete também integram o denominador. Valide a classificação e os valores com o Protheus durante a homologação.</p>
        </div>
      </SuppliesSectionCard>
    </> : null}
  </div>;
}
