import type { CSSProperties, HTMLAttributes, ReactNode, Ref } from "react";

export type ModalFrameProps = {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  /** Encaminha ref ao card (dialog). */
  frameRef?: Ref<HTMLDivElement>;
} & Omit<HTMLAttributes<HTMLDivElement>, "className" | "style" | "children">;

/** Classe canônica do chrome de modal (raio/sombra/header do «Remover…»). */
export function modalFrameClassName(...extra: Array<string | false | null | undefined>): string {
  return ["delpi-ui-modal-frame", ...extra].filter(Boolean).join(" ");
}

/**
 * Container visual canônico de modais do kit.
 * Preferir {@link ModalShell} / `createHostContainedModalShell` — este frame
 * é o card interno (ou uso raro fora do shell).
 */
export function ModalFrame({ children, className, style, frameRef, ...rest }: ModalFrameProps) {
  return (
    <div ref={frameRef} className={modalFrameClassName(className)} style={style} {...rest}>
      {children}
    </div>
  );
}
