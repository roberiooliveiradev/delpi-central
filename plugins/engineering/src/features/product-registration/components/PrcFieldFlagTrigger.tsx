/** Acionador contextual de bandeira — PRC-REF-018 / D16-REF-03.
 * Azul (sem acompanhamento) · Vermelha (OPEN) · Verde (RESOLVED).
 * OPEN prevalece sobre RESOLVED; não empilha ícones. */

import { Flag } from "lucide-react";

import type {
  PrcAttendanceFlag,
  PrcFlagTargetAttribute,
} from "../api/productRegistrationApi";

export type PrcFlagVisualState = "add" | "open" | "resolved";

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

export function findResolvedFieldFlags(
  flags: PrcAttendanceFlag[],
  targetPath: string,
): PrcAttendanceFlag[] {
  return flags
    .filter(
      (f) =>
        f.status === "RESOLVED" &&
        f.subject === "FIELD" &&
        f.targetPath === targetPath,
    )
    .sort((a, b) =>
      String(b.resolvedAt || b.updatedAt || "").localeCompare(
        String(a.resolvedAt || a.updatedAt || ""),
      ),
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

export function findResolvedSupplierFlags(
  flags: PrcAttendanceFlag[],
  supplierCode: string,
  store: string,
  targetAttribute: PrcFlagTargetAttribute,
): PrcAttendanceFlag[] {
  return flags
    .filter(
      (f) =>
        f.status === "RESOLVED" &&
        f.subject === "SUPPLIER_LINK" &&
        f.targetAttribute === targetAttribute &&
        f.supplierKey?.supplierCode === supplierCode &&
        f.supplierKey?.store === store,
    )
    .sort((a, b) =>
      String(b.resolvedAt || b.updatedAt || "").localeCompare(
        String(a.resolvedAt || a.updatedAt || ""),
      ),
    );
}

/** Prioridade visual: OPEN > RESOLVED > add. */
export function resolveFlagVisualState(
  openFlag?: PrcAttendanceFlag | null,
  resolvedFlags?: PrcAttendanceFlag[],
): PrcFlagVisualState {
  if (openFlag) return "open";
  if (resolvedFlags && resolvedFlags.length > 0) return "resolved";
  return "add";
}

export function PrcFieldFlagTrigger({
  openFlag,
  resolvedFlags = [],
  label,
  onOpen,
}: {
  openFlag?: PrcAttendanceFlag | null;
  resolvedFlags?: PrcAttendanceFlag[];
  label: string;
  onOpen: (flag: PrcAttendanceFlag | null) => void;
}) {
  const state = resolveFlagVisualState(openFlag, resolvedFlags);
  const primaryResolved = resolvedFlags[0] || null;
  const classByState: Record<PrcFlagVisualState, string> = {
    add: "engineering-prc__field-flag engineering-prc__field-flag--add",
    open: "engineering-prc__field-flag engineering-prc__field-flag--open",
    resolved:
      "engineering-prc__field-flag engineering-prc__field-flag--resolved",
  };
  const ariaByState: Record<PrcFlagVisualState, string> = {
    add: `Adicionar bandeira em ${label}`,
    open: `Bandeira aberta em ${label}: ${openFlag?.title || "pendência"}`,
    resolved: `Bandeira resolvida em ${label}: ${primaryResolved?.title || "histórico"}`,
  };
  const titleByState: Record<PrcFlagVisualState, string> = {
    add: `Sinalizar ${label}`,
    open: openFlag?.title || "Bandeira aberta",
    resolved: primaryResolved?.title || "Bandeira resolvida",
  };

  return (
    <button
      type="button"
      className={classByState[state]}
      aria-label={ariaByState[state]}
      title={titleByState[state]}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        if (state === "open") onOpen(openFlag || null);
        else if (state === "resolved") onOpen(primaryResolved);
        else onOpen(null);
      }}
    >
      <Flag size={14} aria-hidden />
    </button>
  );
}
