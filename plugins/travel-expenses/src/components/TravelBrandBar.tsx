type Props = {
  className?: string;
};

/** Barra institucional DELPI (4 tons) — alinhada a propostas comerciais / certificados. */
export function TravelBrandBar({ className }: Props) {
  return (
    <div className={["te-brand-bar", className].filter(Boolean).join(" ")} aria-hidden="true">
      <span />
      <span />
      <span />
      <span />
    </div>
  );
}
