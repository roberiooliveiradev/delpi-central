import { useAuthenticatedImage } from "../hooks/useAuthenticatedImage";

type LinkIconProps = {
  title: string;
  imageUrl: string | null;
};

function initialOf(title: string): string {
  const trimmed = title.trim();
  return trimmed ? trimmed.slice(0, 1).toUpperCase() : "?";
}

export function LinkIcon({ title, imageUrl }: LinkIconProps) {
  const preview = useAuthenticatedImage(imageUrl);
  if (preview) {
    return <img className="ma-icon__image" src={preview} alt="" />;
  }
  return <span className="ma-icon__fallback">{initialOf(title)}</span>;
}
