import { SuppliesEntityAvatarLabel, SuppliesEntityLink } from "./suppliesUi";
import { navigatePluginPath } from "./pluginNavigation";
import { buildSupplierDetailPath, buildUserProfileHref } from "./pluginRoutes";
import { canAccessUserProfile } from "./routeAccess";
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
  basePath,
}: {
  person?: PersonRef | null;
  photoPeriod?: PersonPhotoPeriod;
  /**
   * Enables navigation to `/users/:userId` when the person carries a proven
   * Core `user_id` and the session may view that profile (self|admin). Without
   * it — or without a proven identifier — renders informative identity only.
   */
  basePath?: string;
}) {
  const session = useSuppliesSession();
  const { allowedUnits } = session;
  // Single name: Minha DELPI official → TOTVS source name → source code.
  const name = person?.display_name || person?.name || person?.code || "";
  const photoSrc = usePersonPhoto(person?.photo_url, {
    branches: allowedUnits,
    dateFrom: photoPeriod?.dateFrom,
    dateTo: photoPeriod?.dateTo,
  });
  const label = (
    <SuppliesEntityAvatarLabel
      name={name}
      src={photoSrc}
      colorKey={personColorKey(person?.code, person?.protheus_user_id)}
    />
  );
  const targetUserId = (person?.user_id || "").trim();
  if (!basePath || !targetUserId) return label;
  if (!canAccessUserProfile(targetUserId, session)) return label;
  const href = buildUserProfileHref(targetUserId, basePath);
  const personName = name.trim();
  return (
    <SuppliesEntityLink
      href={href}
      title={`Abrir perfil de ${personName}`}
      className="sp-person-identity-link"
      onNavigate={() => navigatePluginPath(href)}
    >
      {label}
    </SuppliesEntityLink>
  );
}
