import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useState,
  type CSSProperties,
  type RefObject,
} from "react";

import { measureTextareaCaretRect } from "../utils/textareaCaretPosition";
import {
  menuAnchorRectFromElement,
  resolveComposerMentionMenuPosition,
  resolveComposerMentionMenuWidth,
  toContainerRelativeRect,
  type ComposerOptionMenuLayout,
} from "../components/shared/overlay/menuPositionUtils";
import {
  resolveAnchoredMenuPortalTarget,
  type AnchoredMenuPortalTarget,
} from "../components/shared/overlay/modalPortalTarget";

type ComposerMentionMenuLayoutState = {
  layout: ComposerOptionMenuLayout;
  menuWidth: number;
  portalTarget: AnchoredMenuPortalTarget;
} | null;

type UseComposerMentionMenuLayoutOptions = {
  open: boolean;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  anchorIndex: number;
  itemCount: number;
  value: string;
};

function resolveContainedScope(textarea: HTMLTextAreaElement | null) {
  const portalTarget = resolveAnchoredMenuPortalTarget(textarea);
  const containerRect = portalTarget.contained
    ? menuAnchorRectFromElement(portalTarget.container)
    : undefined;

  return {
    portalTarget,
    contained: portalTarget.contained,
    containerRect,
  };
}

export function useComposerMentionMenuLayout({
  open,
  textareaRef,
  anchorIndex,
  itemCount,
  value,
}: UseComposerMentionMenuLayoutOptions) {
  const [layoutState, setLayoutState] = useState<ComposerMentionMenuLayoutState>(null);
  const [canUsePortal, setCanUsePortal] = useState(false);

  const updateLayout = useCallback(() => {
    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    const caretRect = measureTextareaCaretRect(textarea, anchorIndex);
    const { portalTarget, contained, containerRect } = resolveContainedScope(textarea);
    const anchorRect =
      contained && containerRect
        ? toContainerRelativeRect(caretRect, containerRect)
        : caretRect;
    const viewport =
      contained && containerRect
        ? { width: containerRect.width, height: containerRect.height }
        : undefined;
    const menuWidth = resolveComposerMentionMenuWidth({
      anchorLeft: anchorRect.left,
      viewport,
    });

    setLayoutState({
      layout: resolveComposerMentionMenuPosition({
        rect: caretRect,
        itemCount,
        menuWidth,
        contained,
        containerRect,
      }),
      menuWidth,
      portalTarget,
    });
  }, [anchorIndex, itemCount, textareaRef, value]);

  useEffect(() => {
    setCanUsePortal(true);
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      setLayoutState(null);
      return;
    }

    updateLayout();

    const textarea = textareaRef.current;

    window.addEventListener("resize", updateLayout);
    window.addEventListener("scroll", updateLayout, true);
    textarea?.addEventListener("scroll", updateLayout);

    return () => {
      window.removeEventListener("resize", updateLayout);
      window.removeEventListener("scroll", updateLayout, true);
      textarea?.removeEventListener("scroll", updateLayout);
    };
  }, [open, updateLayout, textareaRef, value, anchorIndex]);

  const layout = layoutState?.layout ?? null;
  const anchorAbove = Boolean(layout?.anchorAbove);

  const panelStyle: CSSProperties | undefined = layoutState
    ? {
        top: layoutState.layout.top,
        left: layoutState.layout.left,
        width: layoutState.menuWidth,
        maxHeight: layoutState.layout.maxHeight,
        height: "max-content",
        ...(anchorAbove ? { transform: "translateY(-100%)" } : {}),
      }
    : undefined;

  return {
    canUsePortal,
    layoutState,
    panelStyle,
    updateLayout,
  };
}
