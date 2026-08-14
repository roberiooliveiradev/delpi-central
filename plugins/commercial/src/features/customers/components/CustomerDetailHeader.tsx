import { useEffect, useId, useRef, useState } from "react";
import { Calendar, Camera, RefreshCw, Trash2 } from "lucide-react";

import {
  CommercialActionButton,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionHintLabel,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../../app/CommercialFloatingNoticeProvider";
import { navigatePluginView } from "../../../app/pluginNavigation";
import {
  deleteCustomerAvatar,
  upsertCustomerAvatar,
} from "../../../api/customerEnrichmentApi";
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
  /** Rótulo do Path (default Minha carteira). */
  backLabel?: string;
  onReload: () => void;
  onScheduleFollowUp?: () => void;
  canViewProposals?: boolean;
  basePath: string;
  sharedCoverage?: CustomerSharedCoverageItem | null;
  /** Bump after avatar CUD so blob + audit timeline refresh. */
  avatarRefreshKey?: number;
  onAvatarChanged?: () => void;
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
  backLabel = "Minha carteira",
  onReload,
  onScheduleFollowUp,
  canViewProposals = false,
  basePath,
  sharedCoverage,
  avatarRefreshKey = 0,
  onAvatarChanged,
}: CustomerDetailHeaderProps) {
  const { notifySuccess, notifyError } = useCommercialFloatingNotice();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileInputId = useId();
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [localHasAvatar, setLocalHasAvatar] = useState(Boolean(customer?.hasAvatar));

  useEffect(() => {
    setLocalHasAvatar(Boolean(customer?.hasAvatar));
  }, [customer?.hasAvatar, avatarRefreshKey]);

  const status = customer
    ? customer.status ?? resolveCustomerStatus(customer)
    : null;
  const hero = customer ? buildCustomerHeroHighlights(customer) : null;
  const currentLabel = notFound
    ? "Cliente não encontrado"
    : customer?.nome || "Cliente";
  const codeStore = formatEntityCodeStore(codigo, loja) ?? `${codigo}-${loja}`;

  const onUploadAvatar = async (file: File | null | undefined) => {
    if (!customer || !file || avatarBusy) return;
    setAvatarBusy(true);
    try {
      await upsertCustomerAvatar(customer.codigo, customer.loja, file);
      setLocalHasAvatar(true);
      notifySuccess("Logo da conta atualizado.");
      onAvatarChanged?.();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao enviar logo.");
    } finally {
      setAvatarBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const onRemoveAvatar = async () => {
    if (!customer || !localHasAvatar || avatarBusy) return;
    setAvatarBusy(true);
    try {
      await deleteCustomerAvatar(customer.codigo, customer.loja);
      setLocalHasAvatar(false);
      notifySuccess("Logo da conta removido.");
      onAvatarChanged?.();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao remover logo.");
    } finally {
      setAvatarBusy(false);
    }
  };

  return (
    <div className="cm-customer-detail-header">
      <CommercialPagePath
        back={{
          label: backLabel,
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
      />

      {customer ? (
        <div className="cm-customer-detail-header__body cm-page-filters">
          <div className="cm-customer-detail-header__avatar-block">
            <button
              type="button"
              className="cm-customer-detail-header__avatar-button"
              aria-label={CM_HELP.customerDetail.avatarChange}
              disabled={avatarBusy}
              onClick={() => fileInputRef.current?.click()}
            >
              <CustomerAvatar
                code={customer.codigo}
                store={customer.loja}
                name={customer.nome}
                hasAvatar={localHasAvatar}
                size="lg"
                refreshKey={avatarRefreshKey}
                previewable={false}
              />
              <span className="cm-customer-detail-header__avatar-overlay" aria-hidden>
                <Camera size={18} />
                <span>Trocar logo</span>
              </span>
            </button>
            <input
              ref={fileInputRef}
              id={fileInputId}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              className="cm-customer-detail-header__file-input"
              onChange={(event) => {
                const file = event.target.files?.[0];
                void onUploadAvatar(file);
              }}
            />
            {localHasAvatar ? (
              <CommercialActionButton
                variant="ghost"
                disabled={avatarBusy}
                onClick={() => void onRemoveAvatar()}
                aria-label={CM_HELP.customerDetail.avatarRemove}
              >
                <Trash2 size={16} aria-hidden="true" />
                Remover logo
              </CommercialActionButton>
            ) : null}
          </div>
          {hero?.nextAction ? (
            <p className="cm-customer-detail-header__next-action">
              Próxima ação: {hero.nextAction}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
