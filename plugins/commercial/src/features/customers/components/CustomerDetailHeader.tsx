import {
  Calendar,
  MapPin,
  RefreshCw,
  UserRound,
} from "lucide-react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialPagePath,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import type { CustomerSummary } from "../types/customerSummary";
import {
  resolveCustomerStatus,
  statusLabel,
} from "../utils/customerListPresentation";
import { CustomerAvatar } from "./CustomerAvatar";

type CustomerDetailHeaderProps = {
  customer: CustomerSummary;
  lastSuccessAt: Date | null;
  refreshing: boolean;
  loading: boolean;
  onBack: () => void;
  backHref: string;
  onReload: () => void;
  onScheduleFollowUp?: () => void;
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

/**
 * Header de perfil do cliente — breadcrumb, avatar, meta e ações.
 */
export function CustomerDetailHeader({
  customer,
  lastSuccessAt,
  refreshing,
  loading,
  onBack,
  backHref,
  onReload,
  onScheduleFollowUp,
}: CustomerDetailHeaderProps) {
  const status = customer.status ?? resolveCustomerStatus(customer);
  const codeStore =
    formatEntityCodeStore(customer.codigo, customer.loja) ??
    `${customer.codigo}-${customer.loja}`;
  const place = locationLabel(customer);

  return (
    <header className="cm-customer-detail-header">
      <CommercialPagePath
        back={{
          label: "Minha carteira",
          href: backHref,
          onNavigate: (event) => {
            event.preventDefault();
            onBack();
          },
        }}
        current={customer.nome || "Cliente"}
      />

      <div className="cm-customer-detail-header__row">
        <div className="cm-customer-detail-header__identity">
          <CustomerAvatar
            code={customer.codigo}
            store={customer.loja}
            name={customer.nome}
            hasAvatar={customer.hasAvatar}
            size="lg"
          />
          <div className="cm-customer-detail-header__titles">
            <div className="cm-customer-detail-header__name-row">
              <h1 className="cm-customer-detail-header__name">
                {customer.nome || "Cliente sem nome"}
              </h1>
              <HelpTooltip
                content={CM_HELP.customerDetail.header}
                ariaLabel="Ajuda: Conta do cliente"
              />
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
            </div>
            <ul className="cm-customer-detail-header__meta">
              <li>
                Código: {customer.codigo}
                <span className="visually-hidden"> ({codeStore})</span>
                {" · "}
                Loja {customer.loja}
              </li>
              {place ? (
                <li>
                  <MapPin size={14} aria-hidden="true" />
                  {place}
                </li>
              ) : null}
              {customer.sellerName ? (
                <li>
                  <UserRound size={14} aria-hidden="true" />
                  Vendedor: {customer.sellerName}
                </li>
              ) : null}
              <li>
                <Calendar size={14} aria-hidden="true" />
                Última atualização: {formatUpdatedAt(lastSuccessAt)}
                {refreshing ? " · Atualizando…" : ""}
              </li>
            </ul>
          </div>
        </div>

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
        </div>
      </div>
    </header>
  );
}
