type Props = {
  size?: "lg" | "md" | "sm";
  className?: string;
};

export function ProcessoFolderIcon({ size = "lg", className }: Props) {
  const sizeClass =
    size === "sm" ? "tm-processo-folder-icon--sm" : size === "md" ? "tm-processo-folder-icon--md" : "";

  return (
    <span className={["tm-processo-folder-icon", sizeClass, className].filter(Boolean).join(" ")} aria-hidden="true">
      <svg viewBox="0 0 64 52" focusable="false">
        <path
          className="tm-processo-folder-icon__back"
          d="M4 12c0-2.2 1.8-4 4-4h14l6 6h32c2.2 0 4 1.8 4 4v26c0 2.2-1.8 4-4 4H8c-2.2 0-4-1.8-4-4V12z"
        />
        <path
          className="tm-processo-folder-icon__tab"
          d="M4 12c0-2.2 1.8-4 4-4h12l4 4h32c2.2 0 4 1.8 4 4v2H4v-2z"
        />
        <path
          className="tm-processo-folder-icon__front"
          d="M4 18h56c2.2 0 4 1.8 4 4v22c0 2.2-1.8 4-4 4H8c-2.2 0-4-1.8-4-4V18z"
        />
      </svg>
    </span>
  );
}
