import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import {
  useCallback,
  useEffect,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";
import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";
import { useDelpiUiPortalTheme } from "../shape/useDelpiUiPortalTheme";

export type FloatingNoticeVariant = "error" | "warning" | "success" | "info";

export type FloatingNoticeAction = {
  label: string;
  onClick: () => void;
};

export type FloatingNoticeItem = {
  id: string;
  message: ReactNode;
  title?: string;
  variant?: FloatingNoticeVariant;
  /** ms até fechar sozinho; `null` mantém até o usuário fechar. */
  autoDismissMs?: number | null;
  /** Ação opcional (ex.: «Tentar novamente» em erros). */
  action?: FloatingNoticeAction;
  /** Chamado ao fechar pelo X (além de remover o item da pilha). */
  onClose?: () => void;
};

export type FloatingNoticeStackClassNames = {
  stack: string;
  notice: string;
  icon: string;
  content: string;
  title: string;
  message: string;
  action: string;
  closeButton: string;
  progress: string;
};

export type FloatingNoticeStackLabels = {
  dismissAriaLabel: string;
  stackAriaLabel: string;
};

export type FloatingNoticeStackProps = {
  items: FloatingNoticeItem[];
  onDismiss: (id: string) => void;
  classNames: FloatingNoticeStackClassNames;
  labels?: Partial<FloatingNoticeStackLabels>;
  /**
   * Auto-dismiss padrão por variante quando o item não define `autoDismissMs`.
   * Erro/aviso permanecem até fechar; sucesso/info fecham sozinhos.
   */
  defaultAutoDismissMs?: Partial<Record<FloatingNoticeVariant, number | null>>;
  /** Escopo CSS do MFE (ex.: `dashboard-cipa`) — portal vai para o body. */
  portalScopeClassName?: string;
};

const DEFAULT_LABELS: FloatingNoticeStackLabels = {
  dismissAriaLabel: "Fechar aviso",
  stackAriaLabel: "Erros e avisos",
};

const VARIANT_AUTO_DISMISS_MS: Record<FloatingNoticeVariant, number | null> = {
  /** Erro/aviso nunca auto-dismiss — só fechar manual (também forçado em resolveAutoDismissMs). */
  error: null,
  warning: null,
  success: 6000,
  info: 6000,
};

const VARIANT_ICONS: Record<FloatingNoticeVariant, ReactNode> = {
  error: <XCircle size={18} aria-hidden="true" />,
  warning: <AlertTriangle size={18} aria-hidden="true" />,
  success: <CheckCircle2 size={18} aria-hidden="true" />,
  info: <Info size={18} aria-hidden="true" />,
};

export function floatingNoticeStackBemClasses(
  prefix: string,
): FloatingNoticeStackClassNames {
  const notice = delpiUiClass(
    `${prefix}-floating-notice`,
    "delpi-ui-floating-notice",
  );
  const element = (name: string) =>
    notice
      .split(/\s+/)
      .map((token) => `${token}__${name}`)
      .join(" ");
  return {
    stack: delpiUiClass(`${prefix}-floating-notices`, "delpi-ui-floating-notices"),
    notice,
    icon: element("icon"),
    content: element("content"),
    title: element("title"),
    message: element("message"),
    action: element("action"),
    closeButton: element("close"),
    progress: element("progress"),
  };
}

function resolveAutoDismissMs(
  variant: FloatingNoticeVariant,
  itemAutoDismissMs: number | null | undefined,
  defaultAutoDismissMs: FloatingNoticeStackProps["defaultAutoDismissMs"],
): number | null {
  /** Erro/aviso só saem com fechar manual — ignoram timer do item ou do host. */
  if (variant === "error" || variant === "warning") {
    return null;
  }
  if (itemAutoDismissMs !== undefined) {
    return itemAutoDismissMs;
  }
  return defaultAutoDismissMs?.[variant] ?? VARIANT_AUTO_DISMISS_MS[variant];
}

function FloatingNotice({
  item,
  onDismiss,
  classNames,
  labels,
  defaultAutoDismissMs,
}: {
  item: FloatingNoticeItem;
  onDismiss: (id: string) => void;
  classNames: FloatingNoticeStackClassNames;
  labels: FloatingNoticeStackLabels;
  defaultAutoDismissMs?: FloatingNoticeStackProps["defaultAutoDismissMs"];
}) {
  const variant = item.variant ?? "error";
  const autoDismissMs = resolveAutoDismissMs(
    variant,
    item.autoDismissMs,
    defaultAutoDismissMs,
  );

  useEffect(() => {
    if (autoDismissMs === null || autoDismissMs === undefined) return;
    const timer = window.setTimeout(() => onDismiss(item.id), autoDismissMs);
    return () => window.clearTimeout(timer);
  }, [autoDismissMs, item.id, onDismiss]);

  const showProgress =
    typeof autoDismissMs === "number" && Number.isFinite(autoDismissMs) && autoDismissMs > 0;

  return (
    <div
      className={withBemModifier(classNames.notice, variant)}
      role={variant === "error" || variant === "warning" ? "alert" : "status"}
      style={
        showProgress
          ? ({
              ["--delpi-ui-floating-notice-dismiss-ms"]: `${autoDismissMs}ms`,
            } as CSSProperties)
          : undefined
      }
    >
      <span className={classNames.icon}>{VARIANT_ICONS[variant]}</span>
      <div className={classNames.content}>
        {item.title ? <strong className={classNames.title}>{item.title}</strong> : null}
        <div className={classNames.message}>{item.message}</div>
        {item.action ? (
          <button
            type="button"
            className={classNames.action}
            onClick={item.action.onClick}
          >
            {item.action.label}
          </button>
        ) : null}
      </div>
      <button
        type="button"
        className={classNames.closeButton}
        aria-label={labels.dismissAriaLabel}
        onClick={() => {
          item.onClose?.();
          onDismiss(item.id);
        }}
      >
        <X size={16} aria-hidden="true" />
      </button>
      {showProgress ? (
        <span className={classNames.progress} aria-hidden="true" />
      ) : null}
    </div>
  );
}

/**
 * Pilha flutuante de erros e avisos (canto superior direito), via portal no
 * `document.body`. Controlado: o chamador mantém a lista e remove no dismiss.
 */
export function FloatingNoticeStack({
  items,
  onDismiss,
  classNames,
  labels,
  defaultAutoDismissMs,
  portalScopeClassName,
}: FloatingNoticeStackProps) {
  const resolvedLabels = { ...DEFAULT_LABELS, ...labels };
  const portalTheme = useDelpiUiPortalTheme(items.length > 0);

  if (items.length === 0 || typeof document === "undefined") {
    return null;
  }

  const scopeClass = [portalScopeClassName, portalTheme.hostClassName]
    .filter(Boolean)
    .join(" ");

  return createPortal(
    <div
      className={scopeClass}
      style={portalTheme.style}
      data-theme={portalTheme.dataTheme ?? undefined}
    >
      <div
        className={classNames.stack}
        style={{ zIndex: DELPI_UI_OVERLAY_Z_INDEX.floatingNotice }}
        aria-label={resolvedLabels.stackAriaLabel}
        aria-live="polite"
      >
        {items.map((item) => (
          <FloatingNotice
            key={item.id}
            item={item}
            onDismiss={onDismiss}
            classNames={classNames}
            labels={resolvedLabels}
            defaultAutoDismissMs={defaultAutoDismissMs}
          />
        ))}
      </div>
    </div>,
    document.body,
  );
}

export type FloatingNoticeInput = Omit<FloatingNoticeItem, "id"> & {
  /** Reaproveitar id substitui o aviso existente (ex.: mesmo campo de erro). */
  id?: string;
};

/** Controlador da pilha: push/dismiss/clear com ids gerados. */
export function useFloatingNotices() {
  const [items, setItems] = useState<FloatingNoticeItem[]>([]);

  const push = useCallback((notice: FloatingNoticeInput | string) => {
    const normalized: FloatingNoticeInput =
      typeof notice === "string" ? { message: notice } : notice;
    const id = normalized.id ?? crypto.randomUUID();
    setItems((prev) => [
      ...prev.filter((item) => item.id !== id),
      { ...normalized, id },
    ]);
    return id;
  }, []);

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const clear = useCallback(() => setItems([]), []);

  return { items, push, dismiss, clear };
}

export type DashboardFloatingNoticeStackProps = Omit<
  FloatingNoticeStackProps,
  "classNames" | "portalScopeClassName"
>;

export function createFloatingNoticeStack(config: {
  prefix: string;
  portalScopeClassName?: string;
  labels?: Partial<FloatingNoticeStackLabels>;
}) {
  const classNames = floatingNoticeStackBemClasses(config.prefix);

  return function DashboardFloatingNoticeStack(
    props: DashboardFloatingNoticeStackProps,
  ) {
    return (
      <FloatingNoticeStack
        classNames={classNames}
        portalScopeClassName={config.portalScopeClassName}
        labels={config.labels}
        {...props}
      />
    );
  };
}
