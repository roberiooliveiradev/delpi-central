import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
} from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import {
  CommercialActionButton,
  CommercialDetailFieldGrid,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { resolvePagePathBack } from "../../../app/commercialNavigationReturn";
import { navigatePluginPath } from "../../../app/pluginNavigation";
import { buildCustomerDetailPath } from "../../../app/pluginRoutes";
import { CUSTOMER_INVOICE_DETAIL_CONTENT } from "../../../content/customerInvoiceContent";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { getCustomerOutboundInvoice } from "../billing/api/customerBillingApi";
import { CustomerInvoiceItems } from "../billing/components/CustomerInvoiceItems";
import type { CustomerInvoice } from "../billing/types/customerBilling";
import { situationLabel } from "../billing/utils/billingPeriod";
import { buildCustomerDetailSearch } from "../utils/customerDetailSection";

type CustomerInvoiceDetailPageProps = {
  basePath: string;
  codigo: string;
  loja: string;
  branch: string;
  invoiceNumber: string;
  invoiceSeries: string;
  search?: string;
};

export function CustomerInvoiceDetailPage({
  basePath,
  codigo,
  loja,
  branch,
  invoiceNumber,
  invoiceSeries,
  search,
}: CustomerInvoiceDetailPageProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [invoice, setInvoice] = useState<CustomerInvoice | null>(null);

  const accountPath =
    buildCustomerDetailPath(basePath, codigo, loja) ?? `${basePath}/customers`;
  const historicoHref = `${accountPath}${buildCustomerDetailSearch("historico")}`;
  const back = resolvePagePathBack(
    search,
    { href: historicoHref, label: CUSTOMER_INVOICE_DETAIL_CONTENT.backToHistory },
    basePath,
  );

  const load = async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCustomerOutboundInvoice(
        { codigo, loja, branch, invoiceNumber, invoiceSeries },
        signal,
      );
      if (signal?.aborted) return;
      setInvoice(data);
    } catch (err) {
      if (signal?.aborted) return;
      setInvoice(null);
      setError(
        err instanceof Error
          ? err.message
          : CUSTOMER_INVOICE_DETAIL_CONTENT.loadError,
      );
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only on key change
  }, [codigo, loja, branch, invoiceNumber, invoiceSeries]);

  const title = `${CUSTOMER_INVOICE_DETAIL_CONTENT.noteLabel} ${invoiceNumber}${
    invoiceSeries ? `-${invoiceSeries}` : ""
  }`;
  const customerName = invoice?.customer_name?.trim() || `${codigo}/${loja}`;

  return (
    <section className="cm-page-stack cm-customer-invoice-detail">
      <CommercialPagePath
        back={{
          label: back.label,
          href: back.href,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(back.href);
          },
        }}
        items={[
          {
            id: "account",
            label: customerName,
            href: accountPath,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginPath(accountPath);
            },
          },
          {
            id: "history",
            label: CUSTOMER_INVOICE_DETAIL_CONTENT.historyCrumb,
            href: historicoHref,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginPath(historicoHref);
            },
          },
        ]}
        current={title}
      />

      <CommercialPageHero
        aria-label={title}
        eyebrow="Conta"
        title={title}
        description={
          loading
            ? CUSTOMER_INVOICE_DETAIL_CONTENT.loading
            : [
                customerName,
                formatOperationalUnitCode(branch),
                invoice ? situationLabel(invoice.situation) : null,
                invoice ? formatCurrency(invoice.total_value) : null,
              ]
                .filter(Boolean)
                .join(" · ")
        }
        actions={
          <CommercialActionButton
            variant="ghost"
            onClick={() => void load()}
            disabled={loading}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />
            {CUSTOMER_INVOICE_DETAIL_CONTENT.refresh}
          </CommercialActionButton>
        }
      />

      {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
      {loading ? (
        <CommercialLoadingCard title={CUSTOMER_INVOICE_DETAIL_CONTENT.loading} />
      ) : null}

      {!loading && !error && !invoice ? (
        <CommercialStateBanner variant="error">
          {CUSTOMER_INVOICE_DETAIL_CONTENT.notFound}
        </CommercialStateBanner>
      ) : null}

      {!loading && invoice ? (
        <>
          <div className="cm-nav-row">
            <CommercialStatusBadge
              variant={invoice.situation === "return" ? "info" : "success"}
              label={situationLabel(invoice.situation)}
            />
            <CommercialStatusBadge
              variant="info"
              label={`${OPERATIONAL_UNIT_COLUMN_LABEL} ${formatOperationalUnitCode(invoice.branch)}`}
            />
          </div>

          <CommercialSectionCard title={CUSTOMER_INVOICE_DETAIL_CONTENT.headerSection}>
            <CommercialDetailFieldGrid
              fields={[
                {
                  label: CUSTOMER_INVOICE_DETAIL_CONTENT.fields.issueDate,
                  value: formatDisplayDate(invoice.issue_date),
                },
                {
                  label: CUSTOMER_INVOICE_DETAIL_CONTENT.fields.accessKey,
                  value: invoice.access_key || "—",
                },
                {
                  label: CUSTOMER_INVOICE_DETAIL_CONTENT.fields.carrier,
                  value: invoice.carrier || "—",
                },
                {
                  label: CUSTOMER_INVOICE_DETAIL_CONTENT.fields.salesOrder,
                  value: invoice.sales_order || "—",
                },
                {
                  label: CUSTOMER_INVOICE_DETAIL_CONTENT.fields.customerOrder,
                  value: invoice.customer_order || "—",
                },
                {
                  label: CUSTOMER_INVOICE_DETAIL_CONTENT.fields.customer,
                  value:
                    invoice.customer_name ||
                    `${invoice.customer_code}/${invoice.customer_store}`,
                },
                {
                  label: CUSTOMER_INVOICE_DETAIL_CONTENT.fields.totalValue,
                  value: formatCurrency(invoice.total_value),
                },
              ]}
            />
          </CommercialSectionCard>

          <CommercialSectionCard title={CUSTOMER_INVOICE_DETAIL_CONTENT.itemsSection}>
            {invoice.items.length > 0 ? (
              <CustomerInvoiceItems items={invoice.items} />
            ) : (
              <p className="cm-customer-invoices__empty">
                {CUSTOMER_INVOICE_DETAIL_CONTENT.emptyItems}
              </p>
            )}
          </CommercialSectionCard>
        </>
      ) : null}
    </section>
  );
}
