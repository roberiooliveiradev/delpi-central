import {
  Award,
  Calendar,
  Eye,
  Flag,
  Handshake,
  Lightbulb,
  Shield,
  Target,
  Users,
  type LucideIcon,
  type LucideProps,
} from "lucide-react";

type IconProps = {
  className?: string;
  size?: number;
};

function lucideIconProps({ className, size = 26 }: IconProps): LucideProps {
  return {
    className,
    size,
    strokeWidth: 2,
    "aria-hidden": true,
  };
}

function CulturaLucideIcon({
  icon: Icon,
  className,
  size = 26,
}: IconProps & { icon: LucideIcon }) {
  return <Icon {...lucideIconProps({ className, size })} />;
}

/** Alvo — ícone oficial Lucide (https://lucide.dev/icons/target) */
export function CulturaPurposeIcon(props: IconProps) {
  return <CulturaLucideIcon icon={Target} {...props} />;
}

/** Bandeira — ícone oficial Lucide (https://lucide.dev/icons/flag) */
export function CulturaMissionIcon(props: IconProps) {
  return <CulturaLucideIcon icon={Flag} {...props} />;
}

/** Olho — ícone oficial Lucide (https://lucide.dev/icons/eye) */
export function CulturaVisionIcon(props: IconProps) {
  return <CulturaLucideIcon icon={Eye} {...props} />;
}

const VALOR_ICONS = [Shield, Award, Lightbulb, Handshake, Users] as const;

export function CulturaValorIcon({
  className,
  index,
  size = 22,
}: IconProps & { index: number }) {
  return (
    <CulturaLucideIcon
      icon={VALOR_ICONS[index % VALOR_ICONS.length]}
      className={className}
      size={size}
    />
  );
}

export function CulturaCalendarIcon(props: IconProps) {
  return <CulturaLucideIcon icon={Calendar} {...props} size={props.size ?? 16} />;
}
