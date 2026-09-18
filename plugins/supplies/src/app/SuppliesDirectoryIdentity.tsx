import { SuppliesEntityAvatarLabel } from "./suppliesUi";
import { personColorKey, supplierColorKey } from "./suppliesDirectory";
import type { PersonRef } from "../features/purchase-requests/types";

type SupplierIdentityProps = {
  name?: string | null;
  code?: string | null;
  store?: string | null;
};

export function SuppliesSupplierIdentity({ name, code, store }: SupplierIdentityProps) {
  return (
    <SuppliesEntityAvatarLabel
      name={name || code || ""}
      secondary={code}
      colorKey={supplierColorKey(code, store)}
    />
  );
}

export function SuppliesPersonIdentity({ person }: { person?: PersonRef | null }) {
  const name = person?.name || person?.code || "";
  const code = person?.code || person?.protheus_user_id || "";
  return (
    <SuppliesEntityAvatarLabel
      name={name}
      secondary={code && code !== name ? code : undefined}
      colorKey={personColorKey(person?.code, person?.protheus_user_id)}
    />
  );
}
