export type MeetingMinuteDocumentMinute = {
  id?: string | null;
  title?: string | null;
  minute_number?: string | null;
  meeting_date?: string | null;
  meeting_type?: string | null;
  location?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  status?: string | null;
  unit_code?: string | null;
};

export type MeetingMinuteDocumentVersion = {
  id?: string | null;
  agenda_html?: string | null;
  body_html?: string | null;
  decisions_html?: string | null;
  pending_html?: string | null;
  observations_html?: string | null;
};

export type MeetingMinuteDocumentParticipant = {
  user_id?: string | null;
  display_name?: string | null;
  role_in_meeting?: string | null;
  is_external?: boolean;
};

export type MeetingMinuteDocumentSigner = {
  id?: string | null;
  user_id?: string | null;
  display_name?: string | null;
  status?: string | null;
};

export type MeetingMinuteDocumentSignature = {
  id?: string | null;
  signer_id?: string | null;
  user_id?: string | null;
  display_name_confirmed?: string | null;
  image_path?: string | null;
  has_image?: boolean | null;
};

export type MeetingMinuteDocumentViewProps = {
  minute: MeetingMinuteDocumentMinute;
  version?: MeetingMinuteDocumentVersion | null;
  participants?: MeetingMinuteDocumentParticipant[];
  signers?: MeetingMinuteDocumentSigner[];
  signatures?: MeetingMinuteDocumentSignature[];
  /** Carrega PNG da assinatura (auth JWT ou token público). */
  getSignatureImage?: (signatureId: string) => Promise<Blob>;
  ariaLabel?: string;
  className?: string;
};
