import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { Trash2, Upload } from "lucide-react";
import {
  ActionButton,
  BackLink,
  DataTable,
  EmptyState,
  SectionCard,
  StateBanner,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  deleteCustomerAvatar,
  enrichPortfolioCustomers,
  fetchCustomerAvatarObjectUrl,
  getMySellerPortfolio,
  upsertCustomerAvatar,
} from "../../api/commercialPortfolioApi";
import { fetchCustomerBillingSeries, getCustomerOutboundInvoices } from "../../api/customerBillingApi";
import { getOpenOrders, resolveOrderStatus } from "../../api/openOrdersApi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { navigatePluginView } from "../../app/pluginNavigation";
import {
  CommercialAvatar,
  CommercialDetailFieldGrid,
  CommercialLoadingCard,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStateBannerClassNames,
  cmStatusBadgeClassNames,
} from "../../app/commercialUi";
import type { OpenOrderItem } from "../../types/openOrders";
import type { CustomerBillingSeriesPoint, CustomerInvoice } from "../../types/billing";
import { customerKey, formatCurrency, formatDate } from "../../shared/format";

type CustomerDetailPageProps = {
  codigo: string;
  loja: string;
  basePath: string;
};

type CustomerIdentity = {
  name: string;
  city: string | null;
  state: string | null;
  billed12m: number;
  lastPurchaseDate: string | null;
};

export function CustomerDetailPage({ codigo, loja, basePath }: CustomerDetailPageProps) {
  const { isAdmin } = usePortfolioScope();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [identity, setIdentity] = useState<CustomerIdentity | null>(null);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [orders, setOrders] = useState<OpenOrderItem[]>([]);

  const [avatarBusy, setAvatarBusy] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [confirmingRemove, setConfirmingRemove] = useState(false);

  const [billingLoading, setBillingLoading] = useState(true);
  const [billingError, setBillingError] = useState<string | null>(null);
  const [billingPoints, setBillingPoints] = useState<CustomerBillingSeriesPoint[]>([]);
  const [invoices, setInvoices] = useState<CustomerInvoice[]>([]);
  const [invoiceSummary, setInvoiceSummary] = useState<{
    totalBilledValue: number;
    invoiceCount: number;
    lastInvoiceDate: string | null;
  } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    Promise.all([
      getMySellerPortfolio(controller.signal),
      getOpenOrders(controller.signal),
      enrichPortfolioCustomers(
        [{ customer_code: codigo, customer_store: loja }],
        controller.signal,
      ),
      fetchCustomerAvatarObjectUrl(codigo, loja, controller.signal),
    ])
      .then(([me, openOrders, enriched, avatar]) => {
        const inPortfolio = (me.portfolio?.customers ?? []).some(
          (customer) =>
            customer.customer_code === codigo && customer.customer_store === loja,
        );
        if (!inPortfolio && !me.is_admin) {
          throw new Error("Cliente fora da sua carteira.");
        }

        const enrich = enriched[0];
        const portfolioCustomer = (me.portfolio?.customers ?? []).find(
          (customer) =>
            customer.customer_code === codigo && customer.customer_store === loja,
        );

        setIdentity({
          name:
            portfolioCustomer?.customer_name?.trim() ||
            enrich?.customer_code ||
            codigo,
          city: enrich?.city ?? null,
          state: enrich?.state ?? null,
          billed12m: enrich?.billed_12m ?? 0,
          lastPurchaseDate: enrich?.last_purchase_date ?? null,
        });
        setAvatarUrl(avatar);

        const filtered = (openOrders.items ?? []).filter((item) => {
          const code = (item.codigo_cadastro ?? "").trim();
          const store = (item.loja_cadastro ?? "").trim();
          return code === codigo && store === loja;
        });
        setOrders(filtered);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar cliente.");
        setIdentity(null);
        setOrders([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => {
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [codigo, loja]);

  useEffect(() => {
    return () => {
      if (avatarUrl?.startsWith("blob:")) {
        URL.revokeObjectURL(avatarUrl);
      }
    };
  }, [avatarUrl]);

  useEffect(() => {
    const controller = new AbortController();
    setBillingLoading(true);
    setBillingError(null);

    Promise.all([
      fetchCustomerBillingSeries(
        [{ customer_code: codigo, customer_store: loja }],
        { months: 12, signal: controller.signal },
      ),
      getCustomerOutboundInvoices(codigo, loja, { pageSize: 10, signal: controller.signal }),
    ])
      .then(([series, invoiceData]) => {
        setBillingPoints(series.points ?? []);
        setInvoices(invoiceData.invoices ?? []);
        setInvoiceSummary({
          totalBilledValue: invoiceData.summary?.total_billed_value ?? 0,
          invoiceCount: invoiceData.summary?.invoice_count ?? 0,
          lastInvoiceDate: invoiceData.summary?.last_invoice_date ?? null,
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setBillingError(
          err instanceof Error ? err.message : "Erro ao carregar faturamento do cliente.",
        );
        setBillingPoints([]);
        setInvoices([]);
        setInvoiceSummary(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setBillingLoading(false);
      });

    return () => controller.abort();
  }, [codigo, loja]);

  async function refreshAvatar() {
    const next = await fetchCustomerAvatarObjectUrl(codigo, loja);
    setAvatarUrl((current) => {
      if (current?.startsWith("blob:")) URL.revokeObjectURL(current);
      return next;
    });
  }

  async function handleFileSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setAvatarBusy(true);
    setAvatarError(null);
    try {
      await upsertCustomerAvatar(codigo, loja, file);
      await refreshAvatar();
    } catch (err: unknown) {
      setAvatarError(err instanceof Error ? err.message : "Erro ao salvar logo do cliente.");
    } finally {
      setAvatarBusy(false);
    }
  }

  async function handleRemoveAvatar() {
    if (!confirmingRemove) {
      setConfirmingRemove(true);
      return;
    }

    setAvatarBusy(true);
    setAvatarError(null);
    try {
      await deleteCustomerAvatar(codigo, loja);
      await refreshAvatar();
    } catch (err: unknown) {
      setAvatarError(err instanceof Error ? err.message : "Erro ao remover logo do cliente.");
    } finally {
      setAvatarBusy(false);
      setConfirmingRemove(false);
    }
  }

  const columns = useMemo<DataTableColumn<OpenOrderItem>[]>(
    () => [
      { key: "pedido", header: "Pedido", render: (row) => row.pedido },
      { key: "produto", header: "Produto", render: (row) => row.produto },
      {
        key: "qty",
        header: "Qtd.",
        align: "right",
        render: (row) => (row.saldo ?? row.quantidade).toLocaleString("pt-BR"),
      },
      { key: "status", header: "Status", render: (row) => resolveOrderStatus(row) },
      { key: "filial", header: "Filial", render: (row) => row.filial },
    ],
    [],
  );

  const invoiceColumns = useMemo<DataTableColumn<CustomerInvoice>[]>(
    () => [
      { key: "invoice", header: "NF", render: (row) => `${row.invoice_number}/${row.invoice_series}` },
      { key: "issueDate", header: "Emissão", render: (row) => formatDate(row.issue_date) },
      {
        key: "situation",
        header: "Situação",
        render: (row) => (
          <StatusBadge
            label={row.situation === "return" ? "Devolução" : "Emitida"}
            variant={row.situation === "return" ? "warning" : "success"}
            classNames={cmStatusBadgeClassNames}
          />
        ),
      },
      {
        key: "value",
        header: "Valor",
        align: "right",
        render: (row) => formatCurrency(row.total_value),
      },
      { key: "salesOrder", header: "Pedido de venda", render: (row) => row.sales_order || "—" },
    ],
    [],
  );

  return (
    <section className="cm-page-stack">
      <BackLink onClick={() => navigatePluginView("customers", { basePath })}>
        Voltar para carteira
      </BackLink>

      {loading ? (
        <CommercialLoadingCard title="Carregando cliente" variant="panel" />
      ) : error ? (
        <StateBanner variant="error" classNames={cmStateBannerClassNames}>
          {error}
        </StateBanner>
      ) : identity ? (
        <>
          <SectionCard
            title={identity.name}
            subtitle={`${codigo} · loja ${loja}`}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <div className="cm-customer-header">
              <div className="cm-customer-avatar-block">
                <CommercialAvatar
                  name={identity.name}
                  colorKey={customerKey(codigo, loja)}
                  src={avatarUrl}
                  alt={`Logo do cliente ${identity.name}`}
                  size="lg"
                />
                {isAdmin ? (
                  <div className="cm-avatar-actions">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      className="cm-avatar-file-input"
                      onChange={handleFileSelected}
                      disabled={avatarBusy}
                    />
                    <ActionButton
                      variant="ghost"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={avatarBusy}
                      aria-label="Enviar logo do cliente"
                    >
                      <Upload size={16} strokeWidth={1.75} aria-hidden="true" />
                      {avatarUrl ? "Substituir logo" : "Enviar logo"}
                    </ActionButton>
                    {avatarUrl ? (
                      <ActionButton
                        variant="ghost"
                        onClick={handleRemoveAvatar}
                        disabled={avatarBusy}
                        aria-label="Remover logo do cliente"
                      >
                        <Trash2 size={16} strokeWidth={1.75} aria-hidden="true" />
                        {confirmingRemove ? "Confirmar remoção?" : "Remover logo"}
                      </ActionButton>
                    ) : null}
                  </div>
                ) : null}
                {avatarError ? (
                  <StateBanner variant="error" classNames={cmStateBannerClassNames}>
                    {avatarError}
                  </StateBanner>
                ) : null}
              </div>
              <CommercialDetailFieldGrid
                fields={[
                  {
                    label: "Localidade",
                    value: [identity.city, identity.state].filter(Boolean).join(" / ") || "—",
                  },
                  { label: "Faturado 12m", value: formatCurrency(identity.billed12m) },
                  { label: "Última compra", value: formatDate(identity.lastPurchaseDate) },
                  { label: "Chave", value: customerKey(codigo, loja) },
                ]}
              />
            </div>
          </SectionCard>

          <SectionCard
            title="Pedidos em aberto deste cliente"
            subtitle={`${orders.length} linha(s)`}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            {orders.length === 0 ? (
              <EmptyState
                title="Sem pedidos em aberto"
                message="Não há pedidos em aberto para este cliente."
                defaultMessage="Não há pedidos em aberto para este cliente."
                classNames={cmEmptyStateClassNames}
              />
            ) : (
              <DataTable
                rows={orders}
                columns={columns}
                rowKey={(row: OpenOrderItem, index: number) =>
                  `${row.pedido}-${row.produto}-${index}`
                }
                classNames={cmDataTableClassNames}
                labels={cmDataTableLabels}
                layout="section"
              />
            )}
          </SectionCard>

          <SectionCard
            title="Faturamento"
            subtitle="Série mensal e notas fiscais de saída (últimos 90 dias)"
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            {billingLoading ? (
              <CommercialLoadingCard title="Carregando faturamento" variant="panel" />
            ) : billingError ? (
              <StateBanner variant="error" classNames={cmStateBannerClassNames}>
                {billingError}
              </StateBanner>
            ) : (
              <>
                {invoiceSummary ? (
                  <CommercialDetailFieldGrid
                    fields={[
                      {
                        label: "Faturado no período",
                        value: formatCurrency(invoiceSummary.totalBilledValue),
                      },
                      { label: "Notas fiscais", value: String(invoiceSummary.invoiceCount) },
                      {
                        label: "Última NF",
                        value: formatDate(invoiceSummary.lastInvoiceDate),
                      },
                    ]}
                  />
                ) : null}

                {billingPoints.length > 0 ? (
                  <ul className="cm-billing-series-list">
                    {billingPoints.map((point) => (
                      <li key={point.month}>
                        <span>{point.label}</span>
                        <strong>{formatCurrency(point.value)}</strong>
                      </li>
                    ))}
                  </ul>
                ) : null}

                {invoices.length === 0 ? (
                  <EmptyState
                    title="Sem notas fiscais"
                    message="Não há notas fiscais de saída no período consultado."
                    defaultMessage="Não há notas fiscais de saída no período consultado."
                    classNames={cmEmptyStateClassNames}
                  />
                ) : (
                  <DataTable
                    rows={invoices}
                    columns={invoiceColumns}
                    rowKey={(row: CustomerInvoice) => row.key}
                    classNames={cmDataTableClassNames}
                    labels={cmDataTableLabels}
                    layout="section"
                  />
                )}
              </>
            )}
          </SectionCard>
        </>
      ) : null}

      <ActionButton variant="ghost" onClick={() => navigatePluginView("customers", { basePath })}>
        Voltar
      </ActionButton>
    </section>
  );
}
