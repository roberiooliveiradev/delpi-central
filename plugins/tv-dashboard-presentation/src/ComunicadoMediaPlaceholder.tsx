type Kind = "image" | "video";
type State = "empty" | "loading" | "error";

type Props = {
  kind: Kind;
  state?: State;
  label?: string;
};

const LABELS: Record<Kind, Record<State, string>> = {
  image: {
    empty: "Imagem",
    loading: "Carregando imagem…",
    error: "Não foi possível carregar a imagem.",
  },
  video: {
    empty: "Vídeo",
    loading: "Carregando vídeo…",
    error: "Não foi possível carregar o vídeo.",
  },
};

function ImageIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor" stroke="none" />
      <path d="m21 15-5-5L5 21" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function VideoIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <rect x="2" y="6" width="14" height="12" rx="2" />
      <path d="m16 10.5 5.2-3.1a.5.5 0 0 1 .8.4v8.4a.5.5 0 0 1-.8.4L16 13.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function LoadingIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <path d="M12 3a9 9 0 1 0 9 9" strokeLinecap="round" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5" strokeLinecap="round" />
      <circle cx="12" cy="16.5" r="0.75" fill="currentColor" stroke="none" />
    </svg>
  );
}

function PlaceholderGraphic({ kind, state }: { kind: Kind; state: State }) {
  if (state === "loading") return <LoadingIcon />;
  if (state === "error") return <ErrorIcon />;
  return kind === "video" ? <VideoIcon /> : <ImageIcon />;
}

/** Ícone + rótulo para blocos de mídia sem arquivo ou em carregamento. */
export function ComunicadoMediaPlaceholder({ kind, state = "empty", label }: Props) {
  const text = label ?? LABELS[kind][state];

  return (
    <div
      className={[
        "tdp-comunicado__placeholder",
        state === "loading" ? "tdp-comunicado__placeholder--loading" : null,
        state === "error" ? "tdp-comunicado__placeholder--error" : null,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <span className="tdp-comunicado__placeholder-icon">
        <PlaceholderGraphic kind={kind} state={state} />
      </span>
      <span className="tdp-comunicado__placeholder-label">{text}</span>
    </div>
  );
}
