import { useEffect, useId, useRef, useState } from "react";
import {
  Calendar,
  MapPin,
  MoreHorizontal,
  Phone,
  RefreshCw,
  UserRound,
} from "lucide-react";
import { BackLink, HelpTooltip } from "@delpi/plugin-ui/index";

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
  onReload: () => void;
  onRegisterContact: () => void;
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
  onReload,
  onRegisterContact,
}: CustomerDetailHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const status = customer.status ?? resolveCustomerStatus(customer);
  const codeStore =
    formatEntityCodeStore(customer.codigo, customer.loja) ??
    `${customer.codigo}-${customer.loja}`;
  const place = locationLabel(customer);

  useEffect(() => {
    if (!menuOpen) return;
    const onDoc = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [menuOpen]);

  return (
    <header className="pva-detail-header">
      <nav className="pva-detail-breadcrumb" aria-label="Navegação">
        <BackLink onClick={onBack}>
          Minha carteira
        </BackLink>
        <span className="pva-detail-breadcrumb__sep" aria-hidden="true">
          /
        </span>
        <span className="pva-detail-breadcrumb__current">
          {customer.nome || "Cliente"}
        </span>
      </nav>

      <div className="pva-detail-header__row">
        <div className="pva-detail-header__identity">
          <CustomerAvatar
            code={customer.codigo}
            store={customer.loja}
            name={customer.nome}
            hasAvatar={customer.hasAvatar}
            size="lg"
          />
          <div className="pva-detail-header__titles">
            <div className="pva-detail-header__name-row">
              <h1 className="pva-detail-header__name">
                {customer.nome || "Cliente sem nome"}
              </h1>
              <HelpTooltip
                content={CM_HELP.customerDetail.header}
                ariaLabel="Ajuda: Conta do cliente"
              />
              <span className={`pva-status-pill pva-status-pill--${status}`}>
                <span className="pva-status-pill__dot" aria-hidden="true" />
                {statusLabel(status)}
              </span>
            </div>
            <ul className="pva-detail-header__meta">
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

        <div className="pva-detail-header__actions">
          <button
            type="button"
            className="pva-btn pva-btn--secondary"
            onClick={onRegisterContact}
          >
            <Phone size={16} aria-hidden="true" />
            Registrar contato
          </button>
          <div className="pva-detail-header__menu" ref={menuRef}>
            <button
              type="button"
              className="pva-btn pva-btn--ghost pva-detail-header__more"
              aria-label="Mais ações"
              aria-expanded={menuOpen}
              aria-controls={menuId}
              onClick={() => setMenuOpen((open) => !open)}
            >
              <MoreHorizontal size={18} aria-hidden="true" />
            </button>
            {menuOpen ? (
              <div id={menuId} className="pva-detail-header__menu-panel" role="menu">
                <button
                  type="button"
                  role="menuitem"
                  className="pva-detail-header__menu-item"
                  disabled={loading || refreshing}
                  onClick={() => {
                    setMenuOpen(false);
                    onReload();
                  }}
                >
                  <RefreshCw
                    size={14}
                    aria-hidden="true"
                    className={refreshing ? "pva-spin" : undefined}
                  />
                  Atualizar dados
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}
