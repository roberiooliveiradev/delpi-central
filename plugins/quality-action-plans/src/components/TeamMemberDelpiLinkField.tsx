import { DelpiUserLinkSection } from "./DelpiUserLinkSection";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";

type Props = {
  idPrefix: string;
  memberUserId: string | null | undefined;
  memberName: string;
  isLeader: boolean;
  onNameChange: (name: string) => void;
  onLink: (userId: string, displayName: string) => void;
  onUnlink: () => void;
};

export function TeamMemberDelpiLinkField({
  idPrefix,
  memberUserId,
  memberName,
  isLeader,
  onNameChange,
  onLink,
  onUnlink,
}: Props) {
  return (
    <DelpiUserLinkSection
      idPrefix={idPrefix}
      userId={memberUserId}
      nameLabel={isLeader ? "Líder" : "Membro"}
      nameHint={isLeader ? PAC_HELP_TOOLTIPS.rnc8d.teamLeader : PAC_HELP_TOOLTIPS.rnc8d.team}
      nameValue={memberName}
      onNameChange={onNameChange}
      onLink={(userId, displayName) => onLink(userId, displayName)}
      onUnlink={onUnlink}
    />
  );
}
