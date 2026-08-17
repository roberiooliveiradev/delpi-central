import "./meetingMinuteDocument.css";

export { MeetingMinuteDocumentView } from "./MeetingMinuteDocumentView";
export { AtaBrandBar, transformaMaisLogoSrc } from "./meetingMinuteBrand";
export {
  isHtmlEmpty,
  mergeAtaContentHtml,
  splitAtaContentForSave,
} from "./meetingMinuteContent";
export {
  ATA_MEETING_TYPE_LABELS,
  ATA_PARTICIPANT_ROLE_LABELS,
  ATA_STATUS_LABELS,
} from "./meetingMinuteLabels";
export {
  ataSignatureProgress,
  ataSignatureStatusLabel,
  ataStatusLabel,
  ataStatusVariant,
  formatAtaMeetingDate,
  tmAtaStatusBadgeClassNames,
} from "./meetingMinuteStatusUi";
export type {
  MeetingMinuteDocumentMinute,
  MeetingMinuteDocumentParticipant,
  MeetingMinuteDocumentSignature,
  MeetingMinuteDocumentSigner,
  MeetingMinuteDocumentVersion,
  MeetingMinuteDocumentViewProps,
} from "./types";
