import { SuppliesEntityAvatarLabel, SuppliesEntityLink } from "./suppliesUi";
import { navigatePluginPath } from "./pluginNavigation";
import { buildSupplierDetailPath } from "./pluginRoutes";
import { personColorKey, supplierColorKey } from "./suppliesDirectory";
import { useSuppliesSession } from "./SuppliesSessionContext";
import { usePersonPhoto } from "./usePersonPhoto";
import type { PersonRef } from "../features/purchase-requests/types";

type SupplierIdentityProps = {
  name?: string | null;
  code?: string | null;
  store?: string | null;
  /**
   * Enables navigation to the E14 supplier page (`/suppliers/:code/:store`)
   * when both `code` and `store` are present. Without `basePath` or when the
   * identity is incomplete (e.g. missing store), renders plain informative
   * identity — never a link from name/CNPJ or an assumed store.
   */
  basePath?: string;
};

export function SuppliesSupplierIdentity({
  name,
  code,
  store,
  basePath,
}: SupplierIdentityProps) {
  const label = (
    <SuppliesEntityAvatarLabel
      name={name || code || ""}
      secondary={code}
      colorKey={supplierColorKey(code, store)}
    />
  );
  const supplierCode = (code || "").trim();
  const supplierStore = (store || "").trim();
  if (!basePath || !supplierCode || !supplierStore) return label;
  const href = buildSupplierDetailPath(supplierCode, supplierStore, basePath);
  const supplierName = (name || code || "").trim();
  return (
    <SuppliesEntityLink
      href={href}
      title={`Abrir cadastro do fornecedor ${supplierName}`}
      className="sp-supplier-identity-link"
      onNavigate={() => navigatePluginPath(href)}
    >
      {label}
    </SuppliesEntityLink>
  );
}

type PersonPhotoPeriod = { dateFrom?: string | null; dateTo?: string | null };

export function SuppliesPersonIdentity({
  person,
  photoPeriod,
}: {
  person?: PersonRef | null;
  photoPeriod?: PersonPhotoPeriod;
}) {
  const { allowedUnits } = useSuppliesSession();
  // Single name: Minha DELPI official → TOTVS source name → source code.
  const name = person?.display_name || person?.name || person?.code || "";
  const photoSrc = usePersonPhoto(person?.photo_url, {
    branches: allowedUnits,
    dateFrom: photoPeriod?.dateFrom,
    dateTo: photoPeriod?.dateTo,
  });
  return (
    <SuppliesEntityAvatarLabel
      name={name}
      src={photoSrc}
      colorKey={personColorKey(person?.code, person?.protheus_user_id)}
    />
  );
}
