import { useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { iconForRequestType } from "../content/requestTypeIcons";
import { InvoiceIssuanceWizard } from "../features/invoice-issuance/ui/InvoiceIssuanceWizard";
import { SchemaFormPage } from "../features/raw-material-creation/SchemaFormPage";
import type { RequestTypeSummary } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsFormActions,
  MyRequestsLoadingState,
  MyRequestsNavigationCard,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
} from "../ui/mrUi";
import { GenericCreateForm } from "./GenericCreateForm";
import { findTypeForDeepLink, readTypeCodeFromSearch } from "./newRequestDeepLink";
import { isInvoiceIssuanceSpecialized, resolveOpenMode } from "./resolveOpenMode";

export function NewRequestPage() {
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeType, setActiveType] = useState<RequestTypeSummary | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    const preferred = readTypeCodeFromSearch();
    setLoading(true);
    listRequestTypes({ signal: ac.signal })
      .then((items) => {
        setTypes(items);
        if (preferred) {
          const match = findTypeForDeepLink(items, preferred);
          if (match) setActiveType(match);
          else setError("Não encontramos esse tipo de solicitação. Escolha um card na lista.");
        }
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => {
        if (!ac.signal.aborted) setLoading(false);
      });
    return () => ac.abort();
  }, []);

  function openType(type: RequestTypeSummary) {
    setError(null);
    setActiveType(type);
  }

  function closeForm() {
    setActiveType(null);
  }

  if (activeType) {
    const openMode = resolveOpenMode(activeType);
    if (isInvoiceIssuanceSpecialized(activeType)) {
      return <InvoiceIssuanceWizard requestType={activeType} onCancel={closeForm} />;
    }
    if (openMode === "schema_driven") {
      return <SchemaFormPage requestType={activeType} onCancel={closeForm} />;
    }
    if (openMode === "specialized") {
      return (
        <AppShell title={activeType.name} canCreate>
          <MyRequestsSectionCard title="Formulário indisponível">
            <MyRequestsStateBanner variant="error">
              Este tipo («{activeType.name}») ainda não tem formulário disponível
              nesta versão. Escolha outro tipo ou fale com o administrador.
            </MyRequestsStateBanner>
            <MyRequestsFormActions>
              <ActionButton type="button" variant="ghost" onClick={closeForm}>
                Voltar
              </ActionButton>
            </MyRequestsFormActions>
          </MyRequestsSectionCard>
        </AppShell>
      );
    }
    return <GenericCreateForm requestType={activeType} onCancel={closeForm} />;
  }

  return (
    <AppShell title="Nova solicitação" canCreate>
      <MyRequestsSectionCard title="Escolha o tipo">
        <div data-help="new" title={MY_REQUESTS_HELP_TOOLTIPS.new.section}>
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          {loading ? (
            <MyRequestsLoadingState message="Carregando tipos…" />
          ) : types.length === 0 ? (
            <MyRequestsEmptyState message="Nenhum tipo de solicitação disponível." />
          ) : (
            <div className="my-requests-type-grid" role="list">
              {types.map((type) => {
                const Icon = iconForRequestType(type.code);
                return (
                  <MyRequestsNavigationCard
                    key={type.code}
                    title={type.name}
                    description={
                      type.description?.trim() ||
                      MY_REQUESTS_HELP_TOOLTIPS.new.type
                    }
                    icon={<Icon size={22} aria-hidden />}
                    onClick={() => openType(type)}
                    aria-label={`Abrir ${type.name}`}
                  />
                );
              })}
            </div>
          )}
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
