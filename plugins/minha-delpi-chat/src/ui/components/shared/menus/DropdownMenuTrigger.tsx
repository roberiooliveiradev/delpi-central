import { MoreHorizontal } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { AnchoredMenuPortal } from "../overlay/AnchoredMenuPortal";
import { ActionMenuPanel, type ActionMenuItem } from "./ActionMenuPanel";

import "./dropdown-menu-trigger.css";

type DropdownMenuTriggerBaseProps = {
  items: ActionMenuItem[];
  menuLabel: string;
  ariaLabel: string;
  title?: string;
  disabled?: boolean;
  iconSize?: number;
  wrapClassName?: string;
  triggerClassName?: string;
  panelClassName?: string;
  scrim?: "transparent" | "backdrop" | "none";
  stopPropagation?: boolean;
  triggerIcon?: ReactNode;
  menuHorizontalAlign?: "start" | "end";
};

type DropdownMenuTriggerControlledProps = DropdownMenuTriggerBaseProps & {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

type DropdownMenuTriggerUncontrolledProps = DropdownMenuTriggerBaseProps & {
  open?: never;
  onOpenChange?: never;
  defaultOpen?: boolean;
};

export type DropdownMenuTriggerProps =
  | DropdownMenuTriggerControlledProps
  | DropdownMenuTriggerUncontrolledProps;

function isControlled(
  props: DropdownMenuTriggerProps,
): props is DropdownMenuTriggerControlledProps {
  return props.open !== undefined;
}

export function DropdownMenuTrigger(props: DropdownMenuTriggerProps) {
  const {
    items,
    menuLabel,
    ariaLabel,
    title = "Opções",
    disabled,
    iconSize = 16,
    wrapClassName = "",
    triggerClassName = "",
    panelClassName = "",
    scrim = "transparent",
    stopPropagation = true,
    triggerIcon,
    menuHorizontalAlign,
  } = props;

  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [internalOpen, setInternalOpen] = useState(
    !isControlled(props) ? (props.defaultOpen ?? false) : false,
  );

  const open = isControlled(props) ? props.open : internalOpen;

  function setOpen(next: boolean) {
    if (isControlled(props)) {
      props.onOpenChange(next);
      return;
    }

    setInternalOpen(next);
  }

  return (
    <div
      className={["mdc-dropdown-menu-trigger", wrapClassName].filter(Boolean).join(" ")}
    >
      <button
        ref={triggerRef}
        type="button"
        className={["mdc-dropdown-menu-trigger__button", triggerClassName]
          .filter(Boolean)
          .join(" ")}
        disabled={disabled}
        onClick={(event) => {
          if (stopPropagation) {
            event.stopPropagation();
          }

          setOpen(!open);
        }}
        aria-label={ariaLabel}
        aria-expanded={open}
        aria-haspopup="menu"
        title={title}
      >
        {triggerIcon ?? <MoreHorizontal size={iconSize} aria-hidden="true" />}
      </button>

      <AnchoredMenuPortal
        open={open}
        triggerRef={triggerRef}
        itemCount={items.length}
        placement="action-menu"
        menuLabel={menuLabel}
        menuRole="menu"
        scrim={scrim}
        menuHorizontalAlign={menuHorizontalAlign}
        panelClassName={panelClassName}
        onClose={() => setOpen(false)}
      >
        <ActionMenuPanel items={items} onItemSelect={() => setOpen(false)} />
      </AnchoredMenuPortal>
    </div>
  );
}
