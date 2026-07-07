type Props = {
  variant?: "empty" | "filled";
  className?: string;
};

export function ProcessoWorkspaceTreeIcon({ variant = "empty", className }: Props) {
  return (
    <span
      className={[
        "tm-processo-workspace-tree-icon",
        variant === "filled" ? "tm-processo-workspace-tree-icon--filled" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-hidden="true"
    >
      <svg viewBox="0 0 64 52" focusable="false">
        <path
          className="tm-processo-workspace-tree-icon__back"
          d="M4 12c0-2.2 1.8-4 4-4h14l6 6h32c2.2 0 4 1.8 4 4v26c0 2.2-1.8 4-4 4H8c-2.2 0-4-1.8-4-4V12z"
        />
        <path
          className="tm-processo-workspace-tree-icon__tab"
          d="M4 12c0-2.2 1.8-4 4-4h12l4 4h32c2.2 0 4 1.8 4 4v2H4v-2z"
        />
        {variant === "filled" ? (
          <>
            <path
              className="tm-processo-workspace-tree-icon__sheet tm-processo-workspace-tree-icon__sheet--back"
              d="M16 24h22c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H16c-1.1 0-2-.9-2-2V26c0-1.1.9-2 2-2z"
            />
            <path
              className="tm-processo-workspace-tree-icon__sheet tm-processo-workspace-tree-icon__sheet--front"
              d="M20 20h22c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H20c-1.1 0-2-.9-2-2V22c0-1.1.9-2 2-2z"
            />
          </>
        ) : null}
        <path
          className="tm-processo-workspace-tree-icon__front"
          d="M4 18h56c2.2 0 4 1.8 4 4v22c0 2.2-1.8 4-4 4H8c-2.2 0-4-1.8-4-4V18z"
        />
      </svg>
    </span>
  );
}
