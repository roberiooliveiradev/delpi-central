import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";
import { useLocation, useNavigate } from "react-router-dom";
import { Sparkles, X } from "lucide-react";

import { HelpTooltip } from "../components/HelpTooltip";
import { AuthContext } from "../state/AuthContext";
import { resolveFederationEntry } from "./appHostEntry";
import {
  buildGlobalDeliaHostProps,
  findAuthorizedDeliaApp,
  isUsableFocusTarget,
  listModalFocusables,
  normalizeAppBasePath,
  resolveDeliaExposedModule,
  resolveFocusReturnTarget,
  resolveModalTabTarget,
  shouldKeepGlobalDeliaPanelOpen,
  shouldRenderGlobalDeliaLauncher,
} from "./globalDeliaSurface";
import { useFederatedRemoteMount } from "./useFederatedRemoteMount";
import { Button } from "../ui-kit";
import "./GlobalDeliaSurface.css";

const GLOBAL_DELIA_HELP =
  "Abre a DÉLIA sem sair do aplicativo atual. A página completa continua disponível em Aplicativos → DÉLIA.";

type GlobalDeliaContextValue = {
  launcherVisible: boolean;
  panelOpen: boolean;
  toggleFrom: (trigger: HTMLElement) => void;
  close: () => void;
  desktopLauncherRef: RefObject<HTMLButtonElement | null>;
  mobileLauncherRef: RefObject<HTMLButtonElement | null>;
};

const GlobalDeliaContext = createContext<GlobalDeliaContextValue | null>(null);

export function GlobalDeliaProvider({ children }: { children: ReactNode }) {
  const { apps, getAccessToken, user } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();
  const [requestedOpen, setRequestedOpen] = useState(false);
  const requestedOpenRef = useRef(false);
  const desktopLauncherRef = useRef<HTMLButtonElement | null>(null);
  const mobileLauncherRef = useRef<HTMLButtonElement | null>(null);
  const openerRef = useRef<HTMLElement | null>(null);

  const deliaApp = useMemo(() => findAuthorizedDeliaApp(apps), [apps]);
  const launcherVisible = shouldRenderGlobalDeliaLauncher({
    apps,
    pathname: location.pathname,
  });
  const panelOpen = shouldKeepGlobalDeliaPanelOpen({
    apps,
    pathname: location.pathname,
    requestedOpen,
  });

  useEffect(() => {
    if (!deliaApp || !launcherVisible) {
      requestedOpenRef.current = false;
      setRequestedOpen(false);
    }
  }, [deliaApp, launcherVisible]);

  const close = useCallback(() => {
    const opener = openerRef.current;
    const desktop = desktopLauncherRef.current;
    const mobile = mobileLauncherRef.current;
    requestedOpenRef.current = false;
    setRequestedOpen(false);
    queueMicrotask(() => {
      const target = resolveFocusReturnTarget(opener, [desktop, mobile]);
      if (isUsableFocusTarget(target)) target.focus();
    });
  }, []);

  const toggleFrom = useCallback((trigger: HTMLElement) => {
    if (!launcherVisible) return;
    if (requestedOpenRef.current) {
      close();
      return;
    }
    openerRef.current = trigger;
    requestedOpenRef.current = true;
    setRequestedOpen(true);
  }, [launcherVisible, close]);

  const hostProps = useMemo(() => {
    if (!deliaApp) return null;
    return buildGlobalDeliaHostProps({
      app: deliaApp,
      pathname: location.pathname,
      search: location.search,
      getAccessToken,
      user,
    });
  }, [deliaApp, location.pathname, location.search, getAccessToken, user]);

  const openFullPage = useCallback(() => {
    if (!deliaApp) return;
    requestedOpenRef.current = false;
    setRequestedOpen(false);
    navigate(normalizeAppBasePath(deliaApp.basePath));
  }, [deliaApp, navigate]);

  const contextValue = useMemo<GlobalDeliaContextValue>(
    () => ({
      launcherVisible,
      panelOpen,
      toggleFrom,
      close,
      desktopLauncherRef,
      mobileLauncherRef,
    }),
    [launcherVisible, panelOpen, toggleFrom, close],
  );

  return (
    <GlobalDeliaContext.Provider value={contextValue}>
      {children}
      {deliaApp && hostProps && panelOpen ? (
        <GlobalDeliaPanel
          entryUrl={resolveFederationEntry(deliaApp)}
          exposedModule={resolveDeliaExposedModule(deliaApp)}
          hostProps={hostProps}
          onClose={close}
          onOpenFullPage={openFullPage}
        />
      ) : null}
    </GlobalDeliaContext.Provider>
  );
}

function useGlobalDelia() {
  return useContext(GlobalDeliaContext);
}

export function GlobalDeliaSidebarLauncher() {
  const ctx = useGlobalDelia();
  if (!ctx?.launcherVisible) return null;

  return (
    <div className="global-delia-launcher-wrap">
      <button
        ref={ctx.desktopLauncherRef}
        type="button"
        className={[
          "sidebar-footer-item",
          "global-delia-launcher",
          ctx.panelOpen ? "is-open" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label="Abrir DÉLIA"
        aria-expanded={ctx.panelOpen}
        aria-controls={ctx.panelOpen ? "global-delia-panel" : undefined}
        data-tour="sidebar-delia"
        onClick={(event) => ctx.toggleFrom(event.currentTarget)}
      >
        <Sparkles size={18} aria-hidden="true" />
        <span>DÉLIA</span>
      </button>
      <HelpTooltip content={GLOBAL_DELIA_HELP} ariaLabel="Ajuda: DÉLIA global" />
    </div>
  );
}

export function GlobalDeliaMobileLauncher() {
  const ctx = useGlobalDelia();
  if (!ctx?.launcherVisible) return null;

  return (
    <button
      ref={ctx.mobileLauncherRef}
      type="button"
      className={`portal-mobile-nav__button ${ctx.panelOpen ? "is-active" : ""}`}
      aria-label="Abrir DÉLIA"
      aria-expanded={ctx.panelOpen}
      data-tour="portal-mobile-nav-delia"
      onClick={(event) => ctx.toggleFrom(event.currentTarget)}
    >
      <Sparkles size={20} strokeWidth={2.1} aria-hidden="true" />
    </button>
  );
}

function GlobalDeliaPanel(props: {
  entryUrl?: string;
  exposedModule: string;
  hostProps: ReturnType<typeof buildGlobalDeliaHostProps>;
  onClose: () => void;
  onOpenFullPage: () => void;
}) {
  const titleId = useId();
  const panelRef = useRef<HTMLElement | null>(null);
  const { hostRef, error, ready } = useFederatedRemoteMount({
    enabled: true,
    entryUrl: props.entryUrl,
    exposedModule: props.exposedModule,
    props: props.hostProps,
  });

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        props.onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const next = resolveModalTabTarget(
        listModalFocusables(panelRef.current),
        document.activeElement,
        event.shiftKey,
      );
      if (!next) return;
      event.preventDefault();
      next.focus();
    }

    window.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [props.onClose]);

  if (typeof document === "undefined") return null;

  return createPortal(
    <div className="global-delia-root" role="presentation">
      <button
        type="button"
        className="global-delia-backdrop"
        aria-label="Fechar painel da DÉLIA"
        onClick={props.onClose}
      />
      <aside
        ref={panelRef}
        id="global-delia-panel"
        className="global-delia-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <header className="global-delia-panel__header">
          <div className="global-delia-panel__heading">
            <h2 id={titleId} className="global-delia-panel__title">
              DÉLIA
            </h2>
            <p className="global-delia-panel__subtitle">Inteligência operacional</p>
          </div>
          <div className="global-delia-panel__actions">
            <Button size="sm" variant="ghost" onClick={props.onOpenFullPage}>
              Abrir página completa
            </Button>
            <button
              type="button"
              className="global-delia-panel__close"
              aria-label="Fechar DÉLIA"
              autoFocus
              onClick={props.onClose}
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>
        </header>
        <div className="global-delia-panel__body">
          {!props.entryUrl ? (
            <p className="global-delia-panel__status">entryUrl não definido.</p>
          ) : null}
          {error ? (
            <p className="global-delia-panel__status" role="alert">
              {error}
            </p>
          ) : null}
          {!ready && !error ? (
            <p className="global-delia-panel__status">Carregando DÉLIA…</p>
          ) : null}
          <div ref={hostRef} className="global-delia-panel__mount" />
        </div>
      </aside>
    </div>,
    document.body,
  );
}
