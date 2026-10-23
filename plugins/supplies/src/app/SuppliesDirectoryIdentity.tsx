import { SuppliesEntityAvatarLabel } from "./suppliesUi";
import { personColorKey, supplierColorKey } from "./suppliesDirectory";
import { usePersonPhoto } from "./usePersonPhoto";
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
  const name = person?.display_name || person?.name || person?.code || "";
  const code = person?.code || person?.protheus_user_id || "";
  const photoSrc = usePersonPhoto(person?.photo_url);
  // When the Core link resolved, the TOTVS source name becomes the
  // secondary line; otherwise keep the source code as before.
  const secondary = person?.display_name
    ? person.name && person.name !== person.display_name
      ? person.name
      : code && code !== name
        ? code
        : undefined
    : code && code !== name
      ? code
      : undefined;
  return (
    <SuppliesEntityAvatarLabel
      name={name}
      secondary={secondary}
      src={photoSrc}
      colorKey={personColorKey(person?.code, person?.protheus_user_id)}
    />
  );
}
