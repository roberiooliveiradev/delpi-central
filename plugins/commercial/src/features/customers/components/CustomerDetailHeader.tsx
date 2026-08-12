import { Calendar, RefreshCw } from "lucide-react";

import {
  CommercialActionButton,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionHintLabel,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerSharedCoverageItem } from "../../../types/portfolio";
import { buildCustomerHeroHighlights } from "../utils/customerHeroHighlights";
import {
  resolveCustomerStatus,
  statusLabel,
} from "../utils/customerListPresentation";
import { CustomerAvatar } from "./CustomerAvatar";
import { CustomerSharedCoverageBadge } from "./CustomerSharedCoverageBadge";

type CustomerDetailHeaderProps = {
  customer?: CustomerSummary | null;
  codigo: string;
  loja: string;
  lastSuccessAt: Date | null;
  refreshing: boolean;
  loading: boolean;
  notFound?: boolean;
  onBack: () => void;
  backHref: string;
  onReload: () => void;
  onScheduleFollowUp?: () => void;
  canViewProposals?: boolean;
  basePath: string;
  sharedCoverage?: CustomerSharedCoverageItem | null;
};

function formatUpdatedAt(value: Date | null): string {
  if (!value) return "—";
  return value.toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function locationLabel(customer: CustomerSummary): string | null {
  const city = customer.city?.trim();
  const state = customer.state?.trim();
  if (city && state) return `${city} / ${state}`;
  if (city) return city;
  if (state) return state;
  return null;
}

function buildDescription(customer: CustomerSummary, lastSuccessAt: Date | null, refreshing: boolean): string {
  const codeStore =
    formatEntityCodeStore(customer.codigo, customer.loja) ??
    `${customer.codigo}-${customer.loja}`;
  const parts = [
    codeStore,
    locationLabel(customer),
    customer.sellerName?.trim() ? `Vendedor ${customer.sellerName.trim()}` : null,
    `Atualizado em ${formatUpdatedAt(lastSuccessAt)}${refreshing ? " · Atualizando…" : ""}`,
  ];
  return parts.filter(Boolean).join(" · ");
}

export function CustomerDetailHeader({
  customer,
  codigo,
  loja,
  lastSuccessAt,
  refreshing,
  loading,
  notFound = false,
  onBack,
  backHref,
  onReload,
  onScheduleFollowUp,
  canViewProposals = false,
  basePath,
  sharedCoverage,
}: CustomerDetailHeaderProps) {
  const status = customer
    ? customer.status ?? resolveCustomerStatus(customer)
    : null;
  const hero = customer ? buildCustomerHeroHighlights(customer) : null;
  const currentLabel = notFound
    ? "Cliente não encontrado"
    : customer?.nome || "Cliente";
  const codeStore = formatEntityCodeStore(codigo, loja) ?? `${codigo}-${loja}`;

  return (
    <div className="cm-customer-detail-header">
      <CommercialPagePath
        back={{
          label: "Minha carteira",
          href: backHref,
          onNavigate: (event) => {
            event.preventDefault();
            onBack();
          },
        }}
        current={currentLabel}
      />
      <CommercialPageHero
        aria-label="Conta do cliente"
        eyebrow="Conta"
        title={
          <CommercialSectionHintLabel
            label={customer?.nome || (notFound ? "Cliente fora da carteira" : "Cliente")}
            hint={CM_HELP.customerDetail.header}
          />
        }
        badge={
          status || sharedCoverage?.shared ? (
            <span className="cm-row-actions">
              {status ? (
                <CommercialStatusBadge
                  variant={
                    status === "ativo"
                      ? "success"
                      : status === "atencao"
                        ? "warning"
                        : "neutral"
                  }
                  label={statusLabel(status)}
                />
              ) : null}
              <CustomerSharedCoverageBadge coverage={sharedCoverage} />
            </span>
          ) : undefined
        }
        description={
          customer
            ? buildDescription(customer, lastSuccessAt, refreshing)
            : `Código / loja: ${codeStore}`
        }
        highlights={hero?.highlights}
        actions={
          <div className="cm-customer-detail-header__actions">
            {onScheduleFollowUp ? (
              <CommercialActionButton
                variant="primary"
                onClick={onScheduleFollowUp}
                aria-label={CM_HELP.customerDetail.scheduleFollowUp}
              >
                <Calendar size={16} aria-hidden="true" />
                Agendar follow-up
              </CommercialActionButton>
            ) : null}
            {canViewProposals ? (
              <CommercialActionButton
                variant="ghost"
                onClick={() => navigatePluginView("proposals", { basePath })}
              >
                Propostas gerais
              </CommercialActionButton>
            ) : null}
            {!notFound ? (
              <CommercialActionButton
                variant="ghost"
                disabled={loading || refreshing}
                onClick={onReload}
              >
                <RefreshCw
                  size={16}
                  aria-hidden="true"
                  className={refreshing ? "cm-spin" : undefined}
                />
                {refreshing || loading ? "Atualizando…" : "Atualizar seção"}
              </CommercialActionButton>
            ) : null}
          </div>
        }
      >
        {customer ? (
          <div className="cm-customer-detail-header__body">
            <CustomerAvatar
              code={customer.codigo}
              store={customer.loja}
              name={customer.nome}
              hasAvatar={customer.hasAvatar}
              size="lg"
            />
            {hero?.nextAction ? (
              <p className="cm-customer-detail-header__next-action">
                Próxima ação: {hero.nextAction}
              </p>
            ) : null}
          </div>
        ) : null}
      </CommercialPageHero>
    </div>
  );
}
