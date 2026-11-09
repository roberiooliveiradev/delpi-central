/** Acionador contextual de bandeira por campo / atributo SA5. */

import { Flag } from "lucide-react";

import type {
  PrcAttendanceFlag,
  PrcFlagTargetAttribute,
} from "../api/productRegistrationApi";

export function findOpenFieldFlag(
  flags: PrcAttendanceFlag[],
  targetPath: string,
): PrcAttendanceFlag | undefined {
  return flags.find(
    (f) =>
      f.status === "OPEN" &&
      f.subject === "FIELD" &&
      f.targetPath === targetPath,
  );
}

export function findOpenSupplierFlag(
  flags: PrcAttendanceFlag[],
  supplierCode: string,
  store: string,
  targetAttribute: PrcFlagTargetAttribute,
): PrcAttendanceFlag | undefined {
  return flags.find(
    (f) =>
      f.status === "OPEN" &&
      f.subject === "SUPPLIER_LINK" &&
      f.targetAttribute === targetAttribute &&
      f.supplierKey?.supplierCode === supplierCode &&
      f.supplierKey?.store === store,
  );
}

export function PrcFieldFlagTrigger({
  openFlag,
  label,
  onOpen,
}: {
  openFlag?: PrcAttendanceFlag | null;
  label: string;
  onOpen: () => void;
}) {
  const hasOpen = Boolean(openFlag);
  return (
    <button
      type="button"
      className={
        hasOpen
          ? "engineering-prc__field-flag engineering-prc__field-flag--open"
          : "engineering-prc__field-flag engineering-prc__field-flag--add"
      }
      aria-label={
        hasOpen
          ? `Bandeira aberta em ${label}: ${openFlag?.title || "pendência"}`
          : `Adicionar bandeira em ${label}`
      }
      title={
        hasOpen
          ? openFlag?.title || "Bandeira aberta"
          : `Sinalizar ${label}`
      }
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onOpen();
      }}
    >
      {/* D16-REF-02: acionador sem OPEN usa Flag azul (não Plus). */}
      <Flag size={14} aria-hidden />
    </button>
  );
}
