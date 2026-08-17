// portal/src/ui-kit/form/Textarea.tsx

import {
  forwardRef,
  useEffect,
  useRef,
  type TextareaHTMLAttributes,
} from "react";
import type { ControlSize } from "./Input";
import "./controls.css";

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  size?: ControlSize;
  invalid?: boolean;
  mono?: boolean;
  autoGrow?: boolean;
};

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea(
    {
      size = "md",
      invalid,
      mono,
      autoGrow = false,
      className,
      "aria-invalid": ariaInvalid,
      onChange,
      rows = 3,
      ...rest
    },
    ref,
  ) {
    const innerRef = useRef<HTMLTextAreaElement | null>(null);
    const isInvalid = invalid || ariaInvalid === true || ariaInvalid === "true";

    const setRefs = (node: HTMLTextAreaElement | null) => {
      innerRef.current = node;
      if (typeof ref === "function") ref(node);
      else if (ref) ref.current = node;
    };

    const resize = () => {
      const el = innerRef.current;
      if (!el || !autoGrow) return;
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    };

    useEffect(() => {
      resize();
    }, [rest.value, autoGrow]);

    const classes = [
      "portal-ui-control",
      `portal-ui-control--${size}`,
      mono ? "portal-ui-control--mono" : "",
      className ?? "",
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <textarea
        ref={setRefs}
        className={classes}
        rows={rows}
        aria-invalid={isInvalid || undefined}
        onChange={(e) => {
          onChange?.(e);
          if (autoGrow) resize();
        }}
        {...rest}
      />
    );
  },
);
