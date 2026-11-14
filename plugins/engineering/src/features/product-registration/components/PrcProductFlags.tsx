/** Bandeiras de produto acompanhado (record-scoped, PRC-TRACK) —
 * contexto da página de produto: estado projetado no corte da revisão
 * visualizada (ADR-04) + modal de ciclo de vida (create/edit/resolve/
 * remove — encerradas são terminais, sem reopen). */

import {
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Flag } from "lucide-react";

import type { PrcRecordFlag } from "../api/productRegistrationApi";
import type { FlagTargetContext } from "./PrcFlagModal";
import { PrcProductFlagModal } from "./PrcProductFlagModal";
import { PrcProductFlagsCtx } from "./prcProductFlagsContext";

const Ctx = PrcProductFlagsCtx;

export function PrcProductFlagsProvider({
  recordId,
  flags,
  allowedActions,
  isCurrentRevision,
  onChanged,
  children,
}: {
  recordId: string;
  flags: PrcRecordFlag[];
  allowedActions: string[];
  isCurrentRevision: boolean;
  onChanged: () => void;
  children: ReactNode;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalFlag, setModalFlag] = useState<PrcRecordFlag | null>(null);
  const [modalTarget, setModalTarget] = useState<FlagTargetContext>({
    subject: "FIELD",
    targetPath: "description",
  });

  const openTarget = useCallback(
    (target: FlagTargetContext, flag?: PrcRecordFlag | null) => {
      setModalTarget(target);
      setModalFlag(flag ?? null);
      setModalOpen(true);
    },
    [],
  );

  const value = useMemo(
    () => ({
      recordId,
      flags,
      allowedActions,
      isCurrentRevision,
      reload: onChanged,
      openTarget,
    }),
    [
      recordId,
      flags,
      allowedActions,
      isCurrentRevision,
      onChanged,
      openTarget,
    ],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      <PrcProductFlagModal
        open={modalOpen}
        recordId={recordId}
        flag={modalFlag}
        target={modalTarget}
        historyFlags={flags}
        allowedActions={allowedActions}
        onClose={() => setModalOpen(false)}
        onChanged={() => {
          setModalOpen(false);
          onChanged();
        }}
      />
    </Ctx.Provider>
  );
}

type RecordFlagVisualState = "add" | "open" | "resolved";

function recordFlagVisualState(
  openFlag: PrcRecordFlag | null | undefined,
  resolvedFlags: PrcRecordFlag[],
): RecordFlagVisualState {
  if (openFlag) return "open";
  if (resolvedFlags.length) return "resolved";
  return "add";
}

/** Trigger contextual por campo/vínculo — mesma UX do D16, estado
 * dirigido por `atStatus` (projeção da revisão exibida). */
export function PrcRecordFlagTrigger({
  openFlag,
  resolvedFlags = [],
  label,
  onOpen,
}: {
  openFlag?: PrcRecordFlag | null;
  resolvedFlags?: PrcRecordFlag[];
  label: string;
  onOpen: (flag: PrcRecordFlag | null) => void;
}) {
  const state = recordFlagVisualState(openFlag, resolvedFlags);
  const primaryResolved = resolvedFlags[0] || null;
  const classByState: Record<RecordFlagVisualState, string> = {
    add: "engineering-prc__field-flag engineering-prc__field-flag--add",
    open: "engineering-prc__field-flag engineering-prc__field-flag--open",
    resolved:
      "engineering-prc__field-flag engineering-prc__field-flag--resolved",
  };
  const ariaByState: Record<RecordFlagVisualState, string> = {
    add: `Adicionar bandeira em ${label}`,
    open: `Bandeira aberta em ${label}: ${openFlag?.title || "pendência"}`,
    resolved: `Bandeira resolvida em ${label}: ${primaryResolved?.title || "histórico"}`,
  };
  const titleByState: Record<RecordFlagVisualState, string> = {
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
