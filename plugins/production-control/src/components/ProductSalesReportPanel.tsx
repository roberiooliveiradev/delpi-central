import { MultiTypeSeriesChart, createDashboardKpiCard } from "@delpi/plugin-ui/index";
import { CalendarDays, Download, Package, Search, TrendingUp, Users } from "lucide-react";
import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { fetchProductSalesReport } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { PpcBranch, ProductSalesReportPayload } from "../types";
import { downloadProductSalesExcel } from "../utils/productSalesExcel";
import { ChartCard } from "./ChartCard";
import { PpcLiquidLoading } from "./PpcLiquidLoading";

const KpiCard = createDashboardKpiCard({ prefix: "ppc", labels: copy.kpi });
const number = (value: number) => new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 0, maximumFractionDigits: 3,
}).format(value);
const labelMonth = (iso: string) => iso.slice(5, 7) + "/" + iso.slice(2, 4);

type Props = { branch: PpcBranch; onRefreshReady?: (reload: () => void) => void };

export function ProductSalesReportPanel({ branch, onRefreshReady }: Props) {
  const [draft, setDraft] = useState("");
  const [productCode, setProductCode] = useState("");
  const [months, setMonths] = useState<12 | 24 | 36>(12);
  const [data, setData] = useState<ProductSalesReportPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [refreshCount, setRefreshCount] = useState(0);
  const reload = useCallback(() => setRefreshCount((n) => n + 1), []);

  useEffect(() => { onRefreshReady?.(reload); }, [onRefreshReady, reload]);
  useEffect(() => {
    if (!productCode) { setData(null); setError(null); return; }
    const controller = new AbortController();
    setLoading(true); setData(null); setError(null);
    fetchProductSalesReport({ branch, productCode, months, signal: controller.signal })
      .then((result) => { if (!controller.signal.aborted) setData(result); })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(
          err instanceof Error ? err.message : "Não foi possível consultar o produto.",
        );
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [branch, productCode, months, refreshCount]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = draft.trim().toUpperCase();
    if (!/^[A-Z0-9_.-]{1,40}$/.test(normalized)) {
      setError("Informe um código válido com até 40 caracteres.");
      return;
    }
    if (normalized === productCode) reload();
    else setProductCode(normalized);
  };

  const monthlyChart = useMemo(
    () => (data?.monthly ?? []).map((row) => ({
      month: labelMonth(row.month), quantity: row.quantity,
    })), [data],
  );
  const yearlyChart = useMemo(() => {
    const sums = new Map<string, number>();
    for (const row of data?.monthly ?? []) {
      const year = row.month.slice(0, 4);
      sums.set(year, (sums.get(year) ?? 0) + row.quantity);
    }
    return [...sums].map(([year, quantity]) => ({ year, quantity }));
  }, [data]);

  const exportExcel = async () => {
    if (!data || exporting) return;
    setExporting(true);
    try { await downloadProductSalesExcel(data); }
    catch (exc) { setError(exc instanceof Error ? exc.message : "Não foi possível exportar o Excel."); }
    finally { setExporting(false); }
  };
  const unit = data?.product.unit || "un.";
  const unitValue = (value: number) => number(value) + " " + unit;

  return (
    <section className="ppc-product-ray" aria-label="Raio-X do produto">
      <form className="ppc-product-ray__filters" onSubmit={submit}>
        <label className="ppc-product-ray__field">
          <span>Código do produto</span>
          <input type="text" value={draft} maxLength={40} required placeholder="Ex.: 90263114"
            autoComplete="off" onChange={(event) => setDraft(event.target.value)} />
        </label>
        <label className="ppc-product-ray__field ppc-product-ray__field--period">
          <span>Histórico de vendas</span>
          <select value={months} onChange={(event) => setMonths(Number(event.target.value) as 12 | 24 | 36)}>
            <option value={12}>12 meses</option><option value={24}>24 meses</option>
            <option value={36}>36 meses</option>
          </select>
        </label>
        <button className="ppc-product-ray__primary" type="submit" disabled={loading}>
          <Search size={17} strokeWidth={1.8} aria-hidden />
          {loading ? "Consultando..." : "Consultar produto"}
        </button>
      </form>
      {error ? <div className="ppc-state ppc-state--error" role="alert">{error}</div> : null}
      {loading ? <PpcLiquidLoading /> : null}
      {!data && !loading && !error ? (
        <div className="ppc-product-ray__empty" role="status">
          <Package size={32} strokeWidth={1.4} aria-hidden />
          <h2>Conheça o histórico do produto</h2>
          <p>Informe o código para visualizar volumes faturados, devoluções, consumo médio e clientes.</p>
        </div>
      ) : null}
      {data ? (
        <>
          <div className="ppc-product-ray__headline">
            <div>
              <span className="ppc-product-ray__eyebrow">RAIO-X · FILIAL {branch} · {months} MESES</span>
              <h2>{data.product.code} <span>{data.product.description}</span></h2>
              <p>{data.period.from} a {data.period.to} · Unidade: {unit} · TOTVS Protheus</p>
            </div>
            <button type="button" className="ppc-product-ray__export" onClick={exportExcel} disabled={exporting}>
              <Download size={16} aria-hidden /> {exporting ? "Preparando..." : "Exportar Excel"}
            </button>
          </div>
          <div className="ppc-reports-kpis ppc-product-ray__kpis">
            <KpiCard title="Volume líquido" value={unitValue(data.summary.total_quantity)} icon={<Package size={22}/>} />
            <KpiCard title="Média semanal" value={unitValue(data.summary.weekly_average)} icon={<TrendingUp size={22}/>} />
            <KpiCard title="Média mensal" value={unitValue(data.summary.monthly_average)} icon={<CalendarDays size={22}/>} />
            <KpiCard title="Média anual equivalente" value={unitValue(data.summary.yearly_average)} icon={<TrendingUp size={22}/>} />
            <KpiCard title="Clientes no período" value={String(data.summary.customer_count)} icon={<Users size={22}/>} />
            <KpiCard title="Devoluções" value={unitValue(data.summary.returned_quantity)} icon={<Package size={22}/>} />
          </div>
          <div className="ppc-product-ray__charts">
            <ChartCard title="Evolução mensal" hint="Quantidade líquida por mês. Meses sem vendas são exibidos com zero.">
              <MultiTypeSeriesChart data={monthlyChart} categoryKey="month"
                series={[{ dataKey: "quantity", name: "Volume líquido", fill: "var(--ppc-accent, #089bdb)" }]}
                chartType="column" height={280} showLegend={false}
                formatY={(value) => number(value)}
                formatTooltipValue={(value) => unitValue(value)}
                margin={{ top: 24, right: 8, left: 0, bottom: 4 }} />
            </ChartCard>
            <ChartCard title="Evolução por ano" hint="Volume dentro da janela selecionada. Anos nas pontas podem ser parciais.">
              <MultiTypeSeriesChart data={yearlyChart} categoryKey="year"
                series={[{ dataKey: "quantity", name: "Volume líquido", fill: "var(--ppc-title, #003866)" }]}
                chartType="column" height={280} showLegend={false} showValueLabels
                formatY={(value) => number(value)}
                formatTooltipValue={(value) => unitValue(value)}
                margin={{ top: 24, right: 8, left: 0, bottom: 4 }} />
            </ChartCard>
          </div>
          <section className="ppc-product-ray__table-card" aria-label="Clientes consumidores">
            <div className="ppc-product-ray__table-heading">
              <div><h3>Clientes consumidores</h3><p>Consumo consolidado por cliente e loja.</p></div>
              <span>{data.customers.length} clientes</span>
            </div>
            {data.customers.length ? (
              <div className="ppc-product-ray__table-scroll">
                <table><thead><tr>
                  <th>Cliente</th><th>Código / loja</th><th>Faturado</th><th>Devolvido</th>
                  <th>Líquido</th><th>Participação bruta</th>
                </tr></thead><tbody>
                  {data.customers.map((customer) => (
                    <tr key={customer.customer_code + ":" + customer.customer_store}>
                      <td>{customer.customer_name}</td>
                      <td>{customer.customer_code}/{customer.customer_store}</td>
                      <td className="ppc-product-ray__numeric">{number(customer.gross_quantity)}</td>
                      <td className="ppc-product-ray__numeric">{number(customer.returned_quantity)}</td>
                      <td className="ppc-product-ray__numeric ppc-product-ray__strong">{number(customer.quantity)}</td>
                      <td className="ppc-product-ray__numeric">
                        {data.summary.gross_quantity > 0
                          ? number(customer.gross_quantity * 100 / data.summary.gross_quantity) + "%"
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody></table>
              </div>
            ) : <p className="ppc-product-ray__no-results">Nenhum faturamento identificado no período.</p>}
          </section>
          <p className="ppc-product-ray__source">
            Fonte: {data.source}. Médias incluem meses sem movimentação. Anos em andamento são
            parciais; devoluções usam a data de digitação.
          </p>
        </>
      ) : null}
    </section>
  );
}
