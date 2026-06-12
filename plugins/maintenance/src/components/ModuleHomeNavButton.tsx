import { ArrowLeft } from "lucide-react";

type ModuleHomeNavButtonProps = {
  label: string;
  targetPath: string;
  onNavigate: (path: string) => void;
  variant?: "home" | "back";
};

export function ModuleHomeNavButton({
  label,
  targetPath,
  onNavigate,
  variant = "home",
}: ModuleHomeNavButtonProps) {
  return (
    <button
      type="button"
      className={`dm-nav__link dm-nav__link--${variant}`}
      onClick={() => onNavigate(targetPath)}
    >
      <ArrowLeft size={14} aria-hidden="true" />
      <span className="dm-nav__link-text">{label}</span>
    </button>
  );
}
