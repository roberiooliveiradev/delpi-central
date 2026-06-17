import type { MouseEventHandler } from "react";

type OverlayScrimProps = {
  className?: string;
  onMouseDown?: MouseEventHandler<HTMLDivElement>;
  as?: "div";
  ariaLabel?: never;
  onClick?: never;
} | {
  className?: string;
  as: "button";
  ariaLabel: string;
  onClick: MouseEventHandler<HTMLButtonElement>;
  onMouseDown?: never;
};

/** Fundo canônico de overlay — camada de clique (transparente), igual ao menu «Mais opções». */
export function OverlayScrim(props: OverlayScrimProps) {
  const className = ["mdc-overlay-scrim", props.className].filter(Boolean).join(" ");

  if (props.as === "button") {
    return (
      <button
        type="button"
        className={className}
        aria-label={props.ariaLabel}
        onClick={props.onClick}
      />
    );
  }

  return (
    <div
      className={className}
      role="presentation"
      aria-hidden="true"
      onMouseDown={props.onMouseDown}
    />
  );
}
