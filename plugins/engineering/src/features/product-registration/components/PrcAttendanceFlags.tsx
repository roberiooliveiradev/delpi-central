/** D16 / PRC-REF-018 — provider + resumo compacto (sem chips de resolvidas). */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { Flag } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import {
  fetchPrcFlags,
  type PrcAttendanceFlag,
} from "../api/productRegistrationApi";
import { PRC_FIELD_LABELS, PRC_FLAG_ACTION_HELP } from "../prcCopy";
import {
  PrcFlagModal,
  type FlagTargetContext,
} from "./PrcFlagModal";

type FlagsCtx = {
  requestId: string;
  flags: PrcAttendanceFlag[];
  openCount: number;
  resolvedCount: number;
  loading: boolean;
  error: string;
  reload: () => Promise<void>;
  openTarget: (
    target: FlagTargetContext,
    flag?: PrcAttendanceFlag | null,
  ) => void;
};

const Ctx = createContext<FlagsCtx | null>(null);

export function usePrcFlagsContext(): FlagsCtx {
  const ctx = useContext(Ctx);
  if (!ctx) {
    throw new Error("usePrcFlagsContext fora de PrcAttendanceFlagsProvider");
  }
  return ctx;
}

export function PrcAttendanceFlagsProvider({
  requestId,
  children,
}: {
  requestId: string;
  children: ReactNode;
}) {
  const [flags, setFlags] = useState<PrcAttendanceFlag[]>([]);
  const [openCount, setOpenCount] = useState(0);
  const [resolvedCount, setResolvedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [modalFlag, setModalFlag] = useState<PrcAttendanceFlag | null>(null);
  const [modalTarget, setModalTarget] = useState<FlagTargetContext>({
    subject: "FIELD",
    targetPath: "description",
  });

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetchPrcFlags(requestId, {
        status: "all",
        page: 1,
        pageSize: 100,
      });
      const data = res.data;
      setFlags(data.items || []);
      setOpenCount(data.openCount ?? 0);
      setResolvedCount(data.resolvedCount ?? 0);
    } catch (err) {
      setError(
        err instanceof HomeApiError
          ? err.message
          : "Não foi possível carregar as bandeiras.",
      );
    } finally {
      setLoading(false);
    }
  }, [requestId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const openTarget = useCallback(
    (target: FlagTargetContext, flag?: PrcAttendanceFlag | null) => {
      setModalTarget(target);
      setModalFlag(flag ?? null);
      setModalOpen(true);
    },
    [],
  );

  const value = useMemo(
    () => ({
      requestId,
      flags,
      openCount,
      resolvedCount,
      loading,
      error,
      reload,
      openTarget,
    }),
    [
      requestId,
      flags,
      openCount,
      resolvedCount,
      loading,
      error,
      reload,
      openTarget,
    ],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      <PrcFlagModal
        open={modalOpen}
        requestId={requestId}
        flag={modalFlag}
        target={modalTarget}
        historyFlags={flags}
        onClose={() => setModalOpen(false)}
        onChanged={reload}
      />
    </Ctx.Provider>
  );
}

/** Resumo compacto PRC-REF-018 — contagens + legenda; sem chips resolvidos. */
export function PrcAttendanceFlagsSummary() {
  const { flags, openCount, resolvedCount, loading, error, openTarget } =
    usePrcFlagsContext();
  const [showLegacy, setShowLegacy] = useState(false);
  const [showLegend, setShowLegend] = useState(false);

  const openFlags = flags.filter((f) => f.status === "OPEN");
  const legacy = flags.filter((f) => f.subject === "GENERAL");

  const jumpTo = (flag: PrcAttendanceFlag) => {
    if (flag.subject === "FIELD" && flag.targetPath) {
      const el = document.getElementById(`prc-field-${flag.targetPath}`);
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
      el?.focus({ preventScroll: true });
    } else if (flag.subject === "SUPPLIER_LINK" && flag.supplierKey) {
      const attr = flag.targetAttribute || "partNumber";
      const id = `prc-supplier-${flag.supplierKey.supplierCode}-${flag.supplierKey.store}-${attr}`;
      document.getElementById(id)?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
    openTarget(
      {
        subject: flag.subject,
        targetPath: flag.targetPath,
        targetAttribute: flag.targetAttribute,
        supplierKey: flag.supplierKey,
        fieldLabel:
          flag.subject === "FIELD" && flag.targetPath
            ? PRC_FIELD_LABELS[flag.targetPath] || flag.targetPath
            : undefined,
      },
      flag,
    );
  };

  return (
    <section
      className="engineering-prc__flags engineering-prc__flags--compact"
      aria-label="Acompanhamento técnico"
    >
      <header className="engineering-prc__flags-head">
        <div className="engineering-prc__flags-title-row">
          <Flag size={16} aria-hidden />
          <h3>Acompanhamento técnico</h3>
          <span className="engineering-prc__flags-count" aria-live="polite">
            {openCount} aberta{openCount === 1 ? "" : "s"} · {resolvedCount}{" "}
            resolvida{resolvedCount === 1 ? "" : "s"}
          </span>
        </div>
        <EngineeringActionButton
          variant="ghost"
          onClick={() => setShowLegend((v) => !v)}
          aria-expanded={showLegend}
          aria-label="Legenda das bandeiras"
        >
          Legenda das bandeiras
        </EngineeringActionButton>
      </header>
      {showLegend ? (
        <ul
          className="engineering-prc__flag-legend"
          aria-label={PRC_FLAG_ACTION_HELP.legend}
        >
          <li>
            <span
              className="engineering-prc__flag-legend-swatch engineering-prc__flag-legend-swatch--add"
              aria-hidden
            >
              <Flag size={14} />
            </span>
            Adicionar acompanhamento
          </li>
          <li>
            <span
              className="engineering-prc__flag-legend-swatch engineering-prc__flag-legend-swatch--open"
              aria-hidden
            >
              <Flag size={14} />
            </span>
            Acompanhamento aberto
          </li>
          <li>
            <span
              className="engineering-prc__flag-legend-swatch engineering-prc__flag-legend-swatch--resolved"
              aria-hidden
            >
              <Flag size={14} />
            </span>
            Acompanhamento resolvido
          </li>
        </ul>
      ) : null}
      {error ? (
        <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
      ) : null}
      {loading ? (
        <p className="engineering-prc__muted">Carregando bandeiras…</p>
      ) : null}
      {!loading && openFlags.length === 0 && resolvedCount === 0 ? (
        <p className="engineering-prc__muted">
          Nenhuma bandeira. Passe o mouse ou foque um campo para sinalizar.
        </p>
      ) : null}
      {openFlags.length > 0 ? (
        <ul className="engineering-prc__flags-chip-list">
          {openFlags.map((f) => {
            const label =
              f.subject === "FIELD" && f.targetPath
                ? PRC_FIELD_LABELS[f.targetPath] || f.targetPath
                : f.subject === "SUPPLIER_LINK"
                  ? `${f.targetAttribute || "?"} · ${f.supplierKey?.supplierCode || "?"}`
                  : "Geral (legado)";
            return (
              <li key={f.id}>
                <button
                  type="button"
                  className="engineering-prc__flags-chip"
                  onClick={() => jumpTo(f)}
                >
                  <Flag size={12} aria-hidden />
                  {label}: {f.title}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
      {legacy.length > 0 ? (
        <div className="engineering-prc__flags-legacy">
          <EngineeringActionButton
            variant="ghost"
            onClick={() => setShowLegacy((v) => !v)}
          >
            {showLegacy
              ? "Ocultar bandeiras antigas sem campo"
              : `Bandeiras antigas sem campo (${legacy.length})`}
          </EngineeringActionButton>
          {showLegacy ? (
            <ul className="engineering-prc__flags-chip-list">
              {legacy.map((f) => (
                <li key={f.id}>
                  <button
                    type="button"
                    className="engineering-prc__flags-chip"
                    onClick={() => jumpTo(f)}
                  >
                    {f.title} · {f.status}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

/** Compat: monta provider + summary (usado na ficha). */
export function PrcAttendanceFlags({ requestId }: { requestId: string }) {
  return (
    <PrcAttendanceFlagsProvider requestId={requestId}>
      <PrcAttendanceFlagsSummary />
    </PrcAttendanceFlagsProvider>
  );
}
