import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { UserRound, X } from "lucide-react";
import {
  createBenchSession,
  endBenchSession,
  fetchCurrentBenchSession,
  isAuthError,
  type BenchSessionSnapshot,
} from "./api.ts";
import {
  identifyErrorMessage,
  normalizeRegistration,
  readStoredSession,
  storeSession,
} from "./operatorSession.ts";
import {
  OperatorSessionContext,
  useOperatorSession,
  type OperatorSessionStatus,
} from "./OperatorSessionContext.ts";

/**
 * C4 — sessão do operador no nível do cockpit (branch + workCenter).
 * Única fonte de verdade: useProductionRun não gerencia mais identidade.
 * A sessão pertence ao posto — persiste entre fila, detalhe, desenho, 3D,
 * timeline e performance; restaurada via GET /bench-sessions/current sem
 * consultar o Portal RH.
 */

type ProviderProps = {
  token: string;
  branch: string;
  workCenter: string | null;
  children: ReactNode;
};

type RestoreState = {
  scope: string | null;
  session: BenchSessionSnapshot | null;
  status: OperatorSessionStatus;
};

export function OperatorSessionProvider({
  token,
  branch,
  workCenter,
  children,
}: ProviderProps) {
  const scope = workCenter ? branch + "|" + workCenter : null;
  const [restore, setRestore] = useState<RestoreState>({
    scope: null,
    session: null,
    status: "restoring",
  });
  const [identifyOpen, setIdentifyOpen] = useState(false);

  // Troca de posto (ou primeira montagem): lê o sessionStorage do novo escopo
  // durante o render — a validação server-side fica no effect abaixo.
  if (restore.scope !== scope) {
    const stored = workCenter ? readStoredSession(branch, workCenter) : null;
    setRestore({
      scope,
      session: stored,
      status: stored ? "restoring" : "anonymous",
    });
    setIdentifyOpen(false);
  }

  // Valida a sessão restaurada na própria bench-session (sem Portal RH).
  // 401 descarta; erro transitório mantém o snapshot local — as operações de
  // produção revalidam o token e descartam em caso de 401.
  useEffect(() => {
    if (!workCenter || restore.scope !== scope) return;
    if (restore.status !== "restoring" || !restore.session) return;
    const storedToken = restore.session.sessionToken;
    let active = true;
    void fetchCurrentBenchSession(token, storedToken)
      .then((validated) => {
        if (!active) return;
        storeSession(branch, workCenter, validated);
        setRestore({ scope, session: validated, status: "identified" });
      })
      .catch((err: unknown) => {
        if (!active) return;
        if (isAuthError(err)) {
          storeSession(branch, workCenter, null);
          setRestore({ scope, session: null, status: "anonymous" });
        } else {
          setRestore((prev) => ({ ...prev, status: "identified" }));
        }
      });
    return () => {
      active = false;
    };
  }, [token, branch, workCenter, scope, restore.scope, restore.status, restore.session]);

  const session = restore.scope === scope ? restore.session : null;
  const status: OperatorSessionStatus =
    restore.scope === scope ? restore.status : "restoring";

  const identify = useCallback(
    async (registration: string): Promise<BenchSessionSnapshot> => {
      if (!workCenter) {
        throw new Error("Selecione o centro de trabalho.");
      }
      const created = await createBenchSession(token, {
        branch,
        workCenter,
        registration: registration.trim(),
      });
      storeSession(branch, workCenter, created);
      setRestore({ scope, session: created, status: "identified" });
      return created;
    },
    [token, branch, workCenter, scope],
  );

  const logout = useCallback(async () => {
    if (!workCenter || !session) return;
    try {
      await endBenchSession(token, session.sessionToken);
    } catch {
      /* sessão já expirada/encerrada: limpa local mesmo assim */
    } finally {
      storeSession(branch, workCenter, null);
      setRestore({ scope, session: null, status: "anonymous" });
    }
  }, [token, branch, workCenter, scope, session]);

  const invalidate = useCallback(() => {
    if (workCenter) storeSession(branch, workCenter, null);
    setRestore({ scope, session: null, status: "anonymous" });
  }, [branch, workCenter, scope]);

  const triggerRef = useRef<HTMLElement | null>(null);

  const openIdentify = useCallback(() => {
    triggerRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setIdentifyOpen(true);
  }, []);

  const closeIdentify = useCallback(() => {
    setIdentifyOpen(false);
    triggerRef.current?.focus();
    triggerRef.current = null;
  }, []);

  return (
    <OperatorSessionContext.Provider
      value={{ session, status, identify, logout, invalidate, openIdentify, identifyOpen }}
    >
      {children}
      {identifyOpen && status !== "identified" ? (
        <IdentifyOperatorModal identify={identify} onClose={closeIdentify} />
      ) : null}
    </OperatorSessionContext.Provider>
  );
}

/**
 * Chip de identidade no hero do cockpit: nome oficial + matrícula, ou o
 * acionador de identificação. hasActiveRun bloqueia a troca enquanto há
 * produção em andamento no posto (handover não pertence à C4).
 */
export function OperatorSessionChip({ hasActiveRun }: { hasActiveRun: boolean }) {
  const { session, status, logout, openIdentify } = useOperatorSession();
  const [blocked, setBlocked] = useState(false);
  const [busy, setBusy] = useState(false);

  if (status === "restoring") {
    return <span className="pcp-pub__operator pcp-pub__operator--loading">…</span>;
  }

  if (!session) {
    return (
      <div className="pcp-pub__operator">
        <UserRound size={16} strokeWidth={2} aria-hidden="true" />
        <span className="pcp-pub__operator-text">
          <span className="pcp-pub__operator-reg">Nenhum operador identificado</span>
        </span>
        <button
          type="button"
          className="pcp-pub__operator-switch pcp-pub__operator-switch--identify"
          onClick={openIdentify}
        >
          Identificar
        </button>
      </div>
    );
  }

  const requestSwitch = async () => {
    if (hasActiveRun) {
      setBlocked(true);
      return;
    }
    setBlocked(false);
    setBusy(true);
    try {
      await logout();
    } finally {
      setBusy(false);
      openIdentify();
    }
  };

  return (
    <div className="pcp-pub__operator">
      <UserRound size={16} strokeWidth={2} aria-hidden="true" />
      <span className="pcp-pub__operator-text">
        <strong>{session.operatorName || session.operatorCode}</strong>
        <span className="pcp-pub__operator-reg">Matrícula {session.operatorCode}</span>
      </span>
      <button
        type="button"
        className="pcp-pub__operator-switch"
        onClick={() => void requestSwitch()}
        disabled={busy}
        aria-label="Trocar operador"
        title="Trocar operador"
      >
        <X size={14} aria-hidden="true" />
      </button>
      {blocked ? (
        <p className="pcp-pub__operator-blocked" role="status">
          Existe uma produção em andamento neste posto. Encerre a produção antes
          de trocar o operador.
        </p>
      ) : null}
    </div>
  );
}

type ModalProps = {
  identify: (registration: string) => Promise<BenchSessionSnapshot>;
  onClose: () => void;
};

function IdentifyOperatorModal({ identify, onClose }: ModalProps) {
  const [registration, setRegistration] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const frame = requestAnimationFrame(() => inputRef.current?.focus());
    return () => cancelAnimationFrame(frame);
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [busy, onClose]);

  const submit = async () => {
    const value = normalizeRegistration(registration);
    if (!value) {
      setError("Informe uma matrícula válida (até 30 caracteres).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await identify(value);
      onClose();
    } catch (err) {
      setError(identifyErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-identify-title"
    >
      <button
        type="button"
        className="pcp-pub-modal__backdrop"
        aria-label="Fechar"
        onClick={onClose}
        disabled={busy}
      />
      <form
        className="pcp-pub-modal__panel pcp-pub-modal__panel--identify"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <div className="pcp-pub-modal__identify-badge" aria-hidden="true">
          <UserRound size={28} strokeWidth={1.8} />
        </div>
        <h3 id="pcp-identify-title" className="pcp-pub-modal__identify-title">
          Identificar operador
        </h3>
        <p className="pcp-pub-modal__identify-sub">
          Informe sua matrícula. O nome é confirmado pelo cadastro oficial.
        </p>
        <label className="pcp-pub__run-field">
          <span>Matrícula</span>
          <input
            ref={inputRef}
            value={registration}
            onChange={(event) => setRegistration(event.target.value)}
            type="text"
            inputMode="numeric"
            autoComplete="off"
            maxLength={30}
            required
            disabled={busy}
            aria-describedby={error ? "pcp-identify-error" : undefined}
          />
        </label>
        <div aria-live="polite">
          {busy ? (
            <p className="pcp-pub__run-note">Validando matrícula…</p>
          ) : null}
          {error ? (
            <p id="pcp-identify-error" className="pcp-pub__run-error">
              {error}
            </p>
          ) : null}
        </div>
        <div className="pcp-pub__run-actions">
          <button
            type="submit"
            className="pcp-pub__btn pcp-pub__btn--primary"
            disabled={busy || !registration.trim()}
          >
            {busy ? "Validando matrícula…" : "Entrar no posto"}
          </button>
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--ghost"
            onClick={onClose}
            disabled={busy}
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
