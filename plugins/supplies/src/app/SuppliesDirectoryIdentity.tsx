import { SuppliesEntityAvatarLabel } from "./suppliesUi";
import { personColorKey, supplierColorKey } from "./suppliesDirectory";
import { useSuppliesSession } from "./SuppliesSessionContext";
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
