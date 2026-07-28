import { delpiUiClass } from "../../utils/delpiUiClass";

export type ScreenLoadingVariant = "embedded" | "fullscreen";

/** `dark` = kiosk / TV; `brand` = tokens `--delpi-ui-*` do host. */
export type ScreenLoadingTone = "dark" | "brand";

export type ScreenLoadingClassNames = {
  root: string;
  glow: string;
  stage: string;
  orbit: string;
  ring: string;
  ringDelayed: string;
  core: string;
  label: string;
  bar: string;
  barFill: string;
};

export type ScreenLoadingProps = {
  /** Texto sob o orbit (ex.: «Carregando»). */
  label?: string;
  /** `fullscreen` preenche o ancestral posicionado (ou viewport fixa). */
  variant?: ScreenLoadingVariant;
  tone?: ScreenLoadingTone;
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
    stage: pair(`${base}__stage`, `${ui}__stage`),
    orbit: pair(`${base}__orbit`, `${ui}__orbit`),
    ring: pair(`${base}__ring`, `${ui}__ring`),
    ringDelayed: pair(`${base}__ring--delayed`, `${ui}__ring--delayed`),
    core: pair(`${base}__core`, `${ui}__core`),
    label: pair(`${base}__label`, `${ui}__label`),
    bar: pair(`${base}__bar`, `${ui}__bar`),
    barFill: pair(`${base}__bar-fill`, `${ui}__bar-fill`),
  };
}

const DEFAULT_CN = screenLoadingBemClasses();

/**
 * Splash de carregamento de tela (orbit + label + barra indeterminada).
 * CSS: `styles/screen-loading.css` (`.delpi-ui-screen-loading*`).
 * Sem strings PT obrigatórias no pacote — `label` vem do host.
 */
export function ScreenLoading({
  label = "Carregando",
  variant = "embedded",
  tone = "dark",
  className,
  classNames = DEFAULT_CN,
}: ScreenLoadingProps) {
  const rootClass = [
    classNames.root,
    `delpi-ui-screen-loading--${variant}`,
    `delpi-ui-screen-loading--${tone}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={label}
    >
      <div className={classNames.glow} aria-hidden="true" />
      <div className={classNames.stage}>
        <div className={classNames.orbit} aria-hidden="true">
          <span className={classNames.ring} />
          <span className={`${classNames.ring} ${classNames.ringDelayed}`} />
          <span className={classNames.core} />
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
}) {
  const classNames = config.classNames ?? DEFAULT_CN;
  const defaultLabel = config.defaultLabel ?? "Carregando";
  const defaultVariant = config.variant ?? "embedded";
  const defaultTone = config.tone ?? "dark";

  return function DashboardScreenLoading(props: {
    label?: string;
    variant?: ScreenLoadingVariant;
    tone?: ScreenLoadingTone;
    className?: string;
  }) {
    return (
      <ScreenLoading
        classNames={classNames}
        label={props.label ?? defaultLabel}
        variant={props.variant ?? defaultVariant}
        tone={props.tone ?? defaultTone}
        className={props.className}
      />
    );
  };
}
