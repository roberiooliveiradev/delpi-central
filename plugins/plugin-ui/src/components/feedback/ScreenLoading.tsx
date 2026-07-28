import { useEffect, useId, useRef, useState } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { BrandLightningLayer } from "./BrandLightningLayer";
import { BrandMark } from "./BrandMark";

export type ScreenLoadingVariant = "embedded" | "fullscreen";

/** `dark` = kiosk / TV; `brand` = tokens `--delpi-ui-*` do host. */
export type ScreenLoadingTone = "dark" | "brand";

export type ScreenLoadingClassNames = {
  root: string;
  glow: string;
  lightning: string;
  lightningLine: string;
  lightningBranch: string;
  stage: string;
  mark: string;
  label: string;
  bar: string;
  barFill: string;
};

export type ScreenLoadingProps = {
  /** Texto sob a marca (ex.: «Carregando»). */
  label?: string;
  /** `fullscreen` preenche o ancestral posicionado (ou viewport fixa). */
  variant?: ScreenLoadingVariant;
  tone?: ScreenLoadingTone;
  /**
   * Raios a partir do swoosh.
   * Default: ligado em `tone=dark` ou `variant=fullscreen`; desligado em brand/embedded.
   */
  showLightning?: boolean;
  className?: string;
  classNames?: ScreenLoadingClassNames;
};

export function screenLoadingBemClasses(prefix = "delpi-ui"): ScreenLoadingClassNames {
  const base = `${prefix}-screen-loading`;
  const ui = "delpi-ui-screen-loading";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(base, ui),
    glow: pair(`${base}__glow`, `${ui}__glow`),
    lightning: pair(`${base}__lightning`, `${ui}__lightning`),
    lightningLine: pair(`${base}__lightning-line`, `${ui}__lightning-line`),
    lightningBranch: pair(`${base}__lightning-branch`, `${ui}__lightning-branch`),
    stage: pair(`${base}__stage`, `${ui}__stage`),
    mark: pair(`${base}__mark`, `${ui}__mark`),
    label: pair(`${base}__label`, `${ui}__label`),
    bar: pair(`${base}__bar`, `${ui}__bar`),
    barFill: pair(`${base}__bar-fill`, `${ui}__bar-fill`),
  };
}

const DEFAULT_CN = screenLoadingBemClasses();

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReduced(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);
  return reduced;
}

/**
 * Splash de carregamento de tela (marca + raios brandados + label + barra).
 * CSS: `styles/screen-loading.css` (`.delpi-ui-screen-loading*`).
 */
export function ScreenLoading({
  label = "Carregando",
  variant = "embedded",
  tone = "dark",
  showLightning,
  className,
  classNames = DEFAULT_CN,
}: ScreenLoadingProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });
  const reducedMotion = usePrefersReducedMotion();
  const gradientScopeId = useId();

  const lightningEnabled =
    showLightning ?? (tone === "dark" || variant === "fullscreen");

  useEffect(() => {
    const el = rootRef.current;
    if (!el || typeof ResizeObserver === "undefined") {
      if (el) {
        const rect = el.getBoundingClientRect();
        setSize({ width: Math.round(rect.width), height: Math.round(rect.height) });
      }
      return;
    }
    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      setSize({ width: Math.round(width), height: Math.round(height) });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const rootClass = [
    classNames.root,
    `delpi-ui-screen-loading--${variant}`,
    `delpi-ui-screen-loading--${tone}`,
    lightningEnabled ? "delpi-ui-screen-loading--lightning" : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const origin = {
    x: size.width / 2,
    y: size.height / 2 - Math.min(28, size.height * 0.04),
  };

  return (
    <div
      ref={rootRef}
      className={rootClass}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={label}
      data-gradient-scope={gradientScopeId}
    >
      <div className={classNames.glow} aria-hidden="true" />
      {lightningEnabled && size.width > 0 ? (
        <BrandLightningLayer
          className={classNames.lightning}
          lineClassName={classNames.lightningLine}
          branchClassName={classNames.lightningBranch}
          width={size.width}
          height={size.height}
          origin={origin}
          density={variant === "fullscreen" ? "medium" : "low"}
          reducedMotion={reducedMotion}
        />
      ) : null}
      <div className={classNames.stage}>
        <div className={classNames.mark} aria-hidden="true">
          <BrandMark tone={tone === "brand" ? "brand" : "dark"} />
        </div>
        <p className={classNames.label}>{label}</p>
        <div className={classNames.bar} aria-hidden="true">
          <span className={classNames.barFill} />
        </div>
      </div>
    </div>
  );
}

export function createDashboardScreenLoading(config: {
  classNames?: ScreenLoadingClassNames;
  defaultLabel?: string;
  variant?: ScreenLoadingVariant;
  tone?: ScreenLoadingTone;
  showLightning?: boolean;
}) {
  const classNames = config.classNames ?? DEFAULT_CN;
  const defaultLabel = config.defaultLabel ?? "Carregando";
  const defaultVariant = config.variant ?? "embedded";
  const defaultTone = config.tone ?? "dark";

  return function DashboardScreenLoading(props: {
    label?: string;
    variant?: ScreenLoadingVariant;
    tone?: ScreenLoadingTone;
    showLightning?: boolean;
    className?: string;
  }) {
    return (
      <ScreenLoading
        classNames={classNames}
        label={props.label ?? defaultLabel}
        variant={props.variant ?? defaultVariant}
        tone={props.tone ?? defaultTone}
        showLightning={props.showLightning ?? config.showLightning}
        className={props.className}
      />
    );
  };
}
