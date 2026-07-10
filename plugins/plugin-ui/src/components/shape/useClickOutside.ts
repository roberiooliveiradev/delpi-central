import { useEffect, useRef, type RefObject } from "react";

function isInsideNestedModal(target: Node): boolean {
  return target instanceof Element && Boolean(target.closest('[aria-modal="true"]'));
}

export function useClickOutside<T extends HTMLElement>(
  refs: RefObject<T | null>[],
  active: boolean,
  onOutside: () => void,
): void {
  const onOutsideRef = useRef(onOutside);
  onOutsideRef.current = onOutside;

  useEffect(() => {
    if (!active) return;

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      const target = event.target as Node | null;
      if (!target) return;
      const inside = refs.some((ref) => ref.current?.contains(target));
      if (inside || isInsideNestedModal(target)) return;
      onOutsideRef.current();
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("touchstart", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("touchstart", handlePointerDown);
    };
  }, [active, refs]);
}
