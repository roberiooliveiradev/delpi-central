import { useEffect, useMemo, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";

import { listRequestTypes } from "../api/requestsApi";
import { AppShell } from "../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { iconForRequestType } from "../content/requestTypeIcons";
import { InvoiceIssuanceWizard } from "../features/invoice-issuance/ui/InvoiceIssuanceWizard";
import { SchemaFormPage } from "../features/raw-material-creation/SchemaFormPage";
import {
  myRequestsNewPath,
  myRequestsPath,
  navigateMyRequestsPath,
} from "../hooks/myRequestsNavigation";
import { useMyRequestsRouterPath } from "../hooks/useMyRequestsRouterPath";
import { useRequestsPermissions } from "../security/RequestsPermissionsContext";
import { canCreateRequestType } from "../security/requestsAccess";
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
  const access = useRequestsPermissions();
  const { search } = useMyRequestsRouterPath();
  const preferredCode = readTypeCodeFromSearch(search);
  const [types, setTypes] = useState<RequestTypeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeType, setActiveType] = useState<RequestTypeSummary | null>(null);

  const creatableTypes = useMemo(
    () =>
      types.filter((type) =>
        canCreateRequestType(access, type.permission_prefix, type.code),
      ),
    [access, types],
  );

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    listRequestTypes({ signal: ac.signal })
      .then((items) => {
        setTypes(items);
      })
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => {
        if (!ac.signal.aborted) setLoading(false);
      });
    return () => ac.abort();
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!preferredCode) {
      setActiveType(null);
      return;
    }
    const match = findTypeForDeepLink(creatableTypes, preferredCode);
    if (match) {
      setActiveType(match);
      setError(null);
      return;
    }
    setActiveType(null);
    const knownButForbidden = findTypeForDeepLink(types, preferredCode);
    if (knownButForbidden) {
      setError(
        "Você não tem permissão para criar este tipo de solicitação. Escolha outro card ou peça acesso ao administrador.",
      );
      return;
    }
    if (types.length > 0) {
      setError("Não encontramos esse tipo de solicitação. Escolha um card na lista.");
    }
  }, [loading, preferredCode, creatableTypes, types]);

  function openType(type: RequestTypeSummary) {
    setError(null);
    navigateMyRequestsPath(myRequestsNewPath(type.code));
  }

  function closeForm() {
    navigateMyRequestsPath(myRequestsPath("new"));
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
        <AppShell title={activeType.name}>
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
    <AppShell title="Nova solicitação">
      <MyRequestsSectionCard title="Escolha o tipo" hint={MY_REQUESTS_HELP_TOOLTIPS.new.section}>
        <div data-help="new">
          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}
          {loading ? (
            <MyRequestsLoadingState message="Carregando tipos…" />
          ) : creatableTypes.length === 0 ? (
            <MyRequestsEmptyState message="Nenhum tipo de solicitação disponível para o seu perfil." />
          ) : (
            <div className="my-requests-type-grid" role="list">
              {creatableTypes.map((type) => {
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
