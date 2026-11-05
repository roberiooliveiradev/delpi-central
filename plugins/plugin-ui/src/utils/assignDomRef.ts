import type { Ref } from "react";

/**
 * React 19 types `ref` on an element as `Ref<T>`, while `useRef<T>(null)`
 * is `Ref<T | null>`. The callback accepts both without a cast at each call site.
 */
export function assignDomRef<T extends HTMLElement>(
  ref: Ref<T | null> | undefined,
): (node: T | null) => void {
  return (node) => {
    if (typeof ref === "function") {
      ref(node);
      return;
    }
    if (ref) ref.current = node;
  };
}
