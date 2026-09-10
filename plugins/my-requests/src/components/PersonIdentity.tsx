import { MyRequestsAvatar } from "../ui/mrUi";

type PersonIdentityProps = {
  name: string | null | undefined;
  userId?: string | null;
  src?: string | null;
  size?: "sm" | "md" | "lg";
};

/**
 * Avatar + name chip for requester / timeline actors.
 * Photo via requests-api BFF blob URL; missing photo → initials.
 */
export function PersonIdentity({
  name,
  userId,
  src = null,
  size = "sm",
}: PersonIdentityProps) {
  const label = (name || "").trim() || "—";
  const colorKey = (userId || "").trim() || label;

  return (
    <span className="my-requests-person-identity">
      <MyRequestsAvatar
        name={label === "—" ? "?" : label}
        colorKey={colorKey}
        src={src}
        size={size}
        previewable={Boolean(src)}
        previewTitle={label === "—" ? undefined : label}
      />
      <span className="my-requests-person-identity__name">{label}</span>
    </span>
  );
}
