import { DelpiUserLinkSection } from "./DelpiUserLinkSection";

type Props = {
  idPrefix: string;
  memberUserId: string | null | undefined;
  memberName: string;
  onLink: (userId: string, displayName: string) => void;
  onUnlink: () => void;
};

export function TeamMemberDelpiLinkField({
  idPrefix,
  memberUserId,
  memberName,
  onLink,
  onUnlink,
}: Props) {
  return (
    <DelpiUserLinkSection
      idPrefix={idPrefix}
      userId={memberUserId}
      displayName={memberName}
      onLink={(userId, displayName) => onLink(userId, displayName)}
      onUnlink={onUnlink}
    />
  );
}
