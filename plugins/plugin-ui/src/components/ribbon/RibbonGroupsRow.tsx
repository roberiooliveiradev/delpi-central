import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import {
  ribbonGroupWidthsNearlyEqual,
  stabilizeCollapsedRibbonGroupIds,
  type RibbonGroupSize,
} from "./resolveCollapsedRibbonGroupIds";

export type RibbonGroupsRowClassNames = {
  root: string;
};

export function ribbonGroupsRowBemClasses(prefix = "delpi-ui"): RibbonGroupsRowClassNames {
  const base = `${prefix}-ribbon-groups`;
  const ui = "delpi-ui-ribbon-groups";
  return {
    root: delpiUiClass(base, ui),
  };
}

type GroupMeasure = {
  expandedWidth: number;
  collapsedWidth: number;
  order: number;
};

type RibbonOverflowContextValue = {
  collapsedIds: ReadonlySet<string>;
  portalScopeClassName?: string;
  registerGroup: (id: string, measure: GroupMeasure) => void;
  unregisterGroup: (id: string) => void;
};

const RibbonOverflowContext = createContext<RibbonOverflowContextValue | null>(null);

export function useRibbonOverflowContext(): RibbonOverflowContextValue | null {
  return useContext(RibbonOverflowContext);
}

export type RibbonGroupsRowProps = {
  children: ReactNode;
  gap?: number;
  className?: string;
  classNames?: RibbonGroupsRowClassNames;
  /** Escopo MFE para popovers (ex.: dashboard-tv-dashboard). */
  portalScopeClassName?: string;
  /** Desliga overflow (sempre expandido) — útil em testes/painéis. */
  overflowEnabled?: boolean;
};

const DEFAULT_CN = ribbonGroupsRowBemClasses();

/**
 * Faixa horizontal de grupos com colapso responsivo (direita → esquerda).
 * Filhos devem ser `RibbonGroup` (ou wrappers) com `groupId`.
 */
export function RibbonGroupsRow({
  children,
  gap = 8,
  className,
  classNames = DEFAULT_CN,
  portalScopeClassName,
  overflowEnabled = true,
}: RibbonGroupsRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const measuresRef = useRef<Map<string, GroupMeasure>>(new Map());
  const [availableWidth, setAvailableWidth] = useState(0);
  const [version, setVersion] = useState(0);

  useLayoutEffect(() => {
    const node = rowRef.current;
    if (!node || typeof ResizeObserver === "undefined") return;
    const update = () => {
      const next = measureRibbonAvailableWidth(node);
      setAvailableWidth((prev) => (prev === next ? prev : next));
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(node);
    if (node.parentElement) observer.observe(node.parentElement);
    return () => observer.disconnect();
  }, []);

  const registerGroup = useCallback((id: string, measure: GroupMeasure) => {
    const prev = measuresRef.current.get(id);
    if (
      prev &&
      ribbonGroupWidthsNearlyEqual(prev.expandedWidth, measure.expandedWidth) &&
      ribbonGroupWidthsNearlyEqual(prev.collapsedWidth, measure.collapsedWidth) &&
      prev.order === measure.order
    ) {
      return;
    }
    measuresRef.current.set(id, measure);
    setVersion((v) => v + 1);
  }, []);

  const unregisterGroup = useCallback((id: string) => {
    if (!measuresRef.current.delete(id)) return;
    setVersion((v) => v + 1);
  }, []);

  const collapsedIdsPrev = useRef<Set<string>>(new Set());
  const collapsedIds = useMemo(() => {
    if (!overflowEnabled || availableWidth <= 0) {
      if (collapsedIdsPrev.current.size === 0) return collapsedIdsPrev.current;
      collapsedIdsPrev.current = new Set();
      return collapsedIdsPrev.current;
    }
    const list: RibbonGroupSize[] = [...measuresRef.current.entries()].map(
      ([id, measure]) => ({
        id,
        expandedWidth: measure.expandedWidth,
        collapsedWidth: measure.collapsedWidth,
        order: measure.order,
      }),
    );
    const prev = collapsedIdsPrev.current;
    const next = stabilizeCollapsedRibbonGroupIds(list, availableWidth, prev, gap);
    if (prev.size === next.size && [...next].every((id) => prev.has(id))) {
      return prev;
    }
    collapsedIdsPrev.current = next;
    return next;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- version sinaliza mudança do Map
  }, [availableWidth, gap, overflowEnabled, version]);

  const ctx = useMemo<RibbonOverflowContextValue>(
    () => ({
      collapsedIds,
      portalScopeClassName,
      registerGroup,
      unregisterGroup,
    }),
    [collapsedIds, portalScopeClassName, registerGroup, unregisterGroup],
  );

  return (
    <RibbonOverflowContext.Provider value={ctx}>
      <div
        ref={rowRef}
        className={[classNames.root, className].filter(Boolean).join(" ")}
        style={{ gap }}
        data-ribbon-overflow={overflowEnabled ? "on" : "off"}
      >
        {children}
      </div>
    </RibbonOverflowContext.Provider>
  );
}

export function measureElementWidth(node: HTMLElement | null): number {
  if (!node) return 0;
  return Math.ceil(node.getBoundingClientRect().width);
}

/** Largura de conteúdo (ignora max-width que comprime o bbox na faixa com scroll). */
export function measureElementContentWidth(node: HTMLElement | null): number {
  if (!node) return 0;
  const box = Math.ceil(node.getBoundingClientRect().width);
  const scroll = Math.ceil(node.scrollWidth);
  return Math.max(box, scroll);
}

/**
 * Largura útil da faixa: o host pai costuma estar limitado ao viewport;
 * o próprio row com overflow-x:auto pode reportar clientWidth ≈ scrollWidth
 * quando o ancestral cresce com o conteúdo — aí o colapso nunca dispara.
 */
export function measureRibbonAvailableWidth(row: HTMLElement | null): number {
  if (!row) return 0;
  const rowClient = row.clientWidth;
  const parent = row.parentElement;
  const parentClient = parent?.clientWidth ?? 0;
  if (parentClient > 0 && row.scrollWidth > rowClient + 1) {
    return Math.min(rowClient, parentClient);
  }
  if (parentClient > 0) {
    return Math.min(rowClient > 0 ? rowClient : parentClient, parentClient);
  }
  return rowClient;
}
