import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ExternalLink, Sparkles, X } from "lucide-react";

import { AuthContext } from "../state/AuthContext";
import { resolveFederationEntry } from "./appHostEntry";
import {
  DELIA_DOCK_DEFAULT_WIDTH,
  DELIA_DOCK_MIN_VIEWPORT_PX,
  DELIA_DOCK_MIN_WIDTH,
  adjustDeliaDockWidth,
  buildGlobalDeliaHostProps,
  clampDeliaDockWidth,
  findAuthorizedDeliaApp,
  isUsableFocusTarget,
  normalizeAppBasePath,
  resolveDeliaDockMaxWidth,
  resolveDeliaExposedModule,
  resolveFocusReturnTarget,
  reclampDeliaDockWidth,
  shouldKeepCompanionDockOpen,
  shouldRenderCompanionHandle,
} from "./globalDeliaDock";
import { useFederatedRemoteMount } from "./useFederatedRemoteMount";
import "./GlobalDeliaDock.css";

export function GlobalDeliaDockProvider({ children }: { children: ReactNode }) {
  const { apps, getAccessToken, user } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();
  const workspaceRef = useRef<HTMLDivElement>(null);
  const handleRef = useRef<HTMLButtonElement>(null);
  const returnFocusToHandle = useRef(false);
  const [requestedOpen, setRequestedOpen] = useState(false);
  const [viewportWidth, setViewportWidth] = useState(DELIA_DOCK_MIN_VIEWPORT_PX);
  const [workspaceWidth, setWorkspaceWidth] = useState(0);
  const [dockWidth, setDockWidth] = useState(DELIA_DOCK_DEFAULT_WIDTH);
  const dockWidthRef = useRef(DELIA_DOCK_DEFAULT_WIDTH);

  const deliaApp = useMemo(() => findAuthorizedDeliaApp(apps), [apps]);
  const handleVisible = shouldRenderCompanionHandle({
    apps,
    pathname: location.pathname,
    viewportWidth,
    workspaceWidth,
  });
  const dockOpen = shouldKeepCompanionDockOpen({
    apps,
    pathname: location.pathname,
    viewportWidth,
    workspaceWidth,
    requestedOpen,
  });

  useEffect(() => {
    const query = window.matchMedia(`(min-width: ${DELIA_DOCK_MIN_VIEWPORT_PX}px)`);
    const sync = () => setViewportWidth(query.matches ? DELIA_DOCK_MIN_VIEWPORT_PX : 0);
    sync();
    query.addEventListener("change", sync);
    return () => query.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    const workspace = workspaceRef.current;
    if (!workspace) return;
    const measure = () => setWorkspaceWidth(workspace.getBoundingClientRect().width);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(workspace);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const next = reclampDeliaDockWidth(dockWidthRef.current, workspaceWidth);
    if (next === dockWidthRef.current) return;
    dockWidthRef.current = next;
    setDockWidth(next);
  }, [workspaceWidth]);

  useEffect(() => {
    if (handleVisible || dockOpen) return;
    setRequestedOpen(false);
  }, [handleVisible, dockOpen]);

  useEffect(() => {
    if (!returnFocusToHandle.current || dockOpen || !handleVisible) return;
    returnFocusToHandle.current = false;
    const target = resolveFocusReturnTarget(handleRef.current, []);
    if (isUsableFocusTarget(target)) target.focus();
  }, [dockOpen, handleVisible]);

  const close = useCallback(() => {
    returnFocusToHandle.current = true;
    setRequestedOpen(false);
  }, []);

  const open = useCallback(() => {
    if (!handleVisible) return;
    setRequestedOpen(true);
  }, [handleVisible]);

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
    setRequestedOpen(false);
    navigate(normalizeAppBasePath(deliaApp.basePath));
  }, [deliaApp, navigate]);

  const applyWidth = useCallback((next: number, available: number) => {
    const clamped = clampDeliaDockWidth(next, available);
    dockWidthRef.current = clamped;
    setDockWidth(clamped);
  }, []);

  const onSeparatorKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLDivElement>) => {
      const next = adjustDeliaDockWidth(dockWidthRef.current, workspaceWidth, event.key);
      if (next === dockWidthRef.current) return;
      event.preventDefault();
      applyWidth(next, workspaceWidth);
    },
    [applyWidth, workspaceWidth],
  );

  const onSeparatorPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      const workspace = workspaceRef.current;
      if (!workspace) return;
      event.preventDefault();
      const bounds = workspace.getBoundingClientRect().width;
      const originX = event.clientX;
      const originWidth = dockWidthRef.current;
      const target = event.currentTarget;
      target.setPointerCapture(event.pointerId);
      target.classList.add("is-dragging");

      const onMove = (moveEvent: PointerEvent) => {
        applyWidth(originWidth + (originX - moveEvent.clientX), bounds);
      };
      const onUp = () => {
        target.classList.remove("is-dragging");
        target.removeEventListener("pointermove", onMove);
        target.removeEventListener("pointerup", onUp);
        target.removeEventListener("pointercancel", onUp);
      };
      target.addEventListener("pointermove", onMove);
      target.addEventListener("pointerup", onUp);
      target.addEventListener("pointercancel", onUp);
    },
    [applyWidth],
  );

  const maxWidth = resolveDeliaDockMaxWidth(workspaceWidth);

  return (
    <div className="global-delia-workspace" ref={workspaceRef}>
      <div className="global-delia-workspace__main">{children}</div>
      {dockOpen && deliaApp && hostProps ? (
        <>
          <div
            className="global-delia-dock-separator"
            role="separator"
            aria-orientation="vertical"
            aria-label="Redimensionar DÉLIA"
            aria-valuemin={DELIA_DOCK_MIN_WIDTH}
            aria-valuemax={maxWidth}
            aria-valuenow={dockWidth}
            tabIndex={0}
            onKeyDown={onSeparatorKeyDown}
            onPointerDown={onSeparatorPointerDown}
          />
          <GlobalDeliaDock
            width={dockWidth}
            entryUrl={resolveFederationEntry(deliaApp)}
            exposedModule={resolveDeliaExposedModule(deliaApp)}
            hostProps={hostProps}
            onClose={close}
            onOpenFullPage={openFullPage}
          />
        </>
      ) : null}
      {handleVisible && !dockOpen ? (
        <button
          ref={handleRef}
          type="button"
          className="global-delia-dock-handle"
          aria-label="Abrir DÉLIA ao lado"
          onClick={open}
        >
          <Sparkles size={16} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}

function GlobalDeliaDock(props: {
  width: number;
  entryUrl?: string;
  exposedModule: string;
  hostProps: ReturnType<typeof buildGlobalDeliaHostProps>;
  onClose: () => void;
  onOpenFullPage: () => void;
}) {
  const dockRef = useRef<HTMLElement>(null);
  const { hostRef, error, ready } = useFederatedRemoteMount({
    enabled: true,
    entryUrl: props.entryUrl,
    exposedModule: props.exposedModule,
    props: props.hostProps,
  });

  useEffect(() => {
    dockRef.current?.focus();
  }, []);

  return (
    <aside
      ref={dockRef}
      className="global-delia-dock"
      style={{ width: props.width }}
      aria-label="DÉLIA"
      tabIndex={-1}
      onKeyDown={(event) => {
        if (event.key !== "Escape") return;
        if (!dockRef.current?.contains(event.target as Node)) return;
        event.stopPropagation();
        props.onClose();
      }}
    >
      <div className="global-delia-dock__rail">
        <span className="global-delia-dock__mark" aria-hidden="true">
          <Sparkles size={16} />
        </span>
        <span className="global-delia-dock__rail-spacer" />
        <button
          type="button"
          className="global-delia-dock__action"
          aria-label="Abrir página completa"
          onClick={props.onOpenFullPage}
        >
          <ExternalLink size={16} aria-hidden="true" />
        </button>
        <button
          type="button"
          className="global-delia-dock__action"
          aria-label="Fechar DÉLIA"
          onClick={props.onClose}
        >
          <X size={16} aria-hidden="true" />
        </button>
      </div>
      <div className="global-delia-dock__body">
        {!props.entryUrl ? (
          <p className="global-delia-dock__status">entryUrl não definido.</p>
        ) : null}
        {error ? (
          <p className="global-delia-dock__status" role="alert">
            {error}
          </p>
        ) : null}
        {!ready && !error ? (
          <p className="global-delia-dock__status">Carregando DÉLIA…</p>
        ) : null}
        <div ref={hostRef} className="global-delia-dock__mount" />
      </div>
    </aside>
  );
}
