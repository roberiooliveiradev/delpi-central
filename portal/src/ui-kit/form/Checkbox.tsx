// portal/src/ui-kit/form/Checkbox.tsx

import {
  forwardRef,
  useEffect,
  useRef,
  type InputHTMLAttributes,
  type ReactNode,
} from "react";
import { Check, Minus } from "lucide-react";
import "./Checkbox.css";

export type CheckboxProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "size"
> & {
  label?: ReactNode;
  indeterminate?: boolean;
};

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  function Checkbox(
    { label, indeterminate = false, className, disabled, checked, ...rest },
    ref,
  ) {
    const innerRef = useRef<HTMLInputElement | null>(null);

    const setRefs = (node: HTMLInputElement | null) => {
      innerRef.current = node;
      if (typeof ref === "function") ref(node);
      else if (ref) ref.current = node;
    };

    useEffect(() => {
      if (innerRef.current) {
        innerRef.current.indeterminate = indeterminate;
      }
    }, [indeterminate]);

    const classes = [
      "portal-ui-checkbox",
      disabled ? "portal-ui-checkbox--disabled" : "",
      className ?? "",
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <label className={classes}>
        <input
          ref={setRefs}
          type="checkbox"
          className="portal-ui-checkbox__input"
          disabled={disabled}
          checked={checked}
          {...rest}
        />
        <span className="portal-ui-checkbox__box" aria-hidden="true">
          {indeterminate ? (
            <Minus size={12} strokeWidth={3} />
          ) : checked ? (
            <Check size={12} strokeWidth={3} />
          ) : null}
        </span>
        {label != null ? (
          <span className="portal-ui-checkbox__label">{label}</span>
        ) : null}
      </label>
    );
  },
);
