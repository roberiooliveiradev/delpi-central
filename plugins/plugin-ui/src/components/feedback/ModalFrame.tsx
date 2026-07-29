import type { CSSProperties, HTMLAttributes, ReactNode } from "react";

/** Ref estrutural — evita conflito entre `@types/react` do MFE e do kit. */
export type ModalFrameRef =
  | ((instance: HTMLDivElement | null) => void)
  | { current: HTMLDivElement | null }
  | null
  | undefined;

export type ModalFrameProps = {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  /** Encaminha ref ao card (dialog). */
  frameRef?: ModalFrameRef;
} & Omit<HTMLAttributes<HTMLDivElement>, "className" | "style" | "children" | "ref">;

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
    <div
      ref={frameRef as never}
      className={modalFrameClassName(className)}
      style={style}
      {...rest}
    >
      {children}
    </div>
  );
}
