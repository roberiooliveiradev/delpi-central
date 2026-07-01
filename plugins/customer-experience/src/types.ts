export type Participant = {
  id: string;
  publicToken: string;
  fullName: string;
  companyName: string;
  visitDate: string;
  participantInfo: string | null;
  thankYouMessage: string | null;
  photoUrl: string;
  qrUrl: string;
  feedbackQrUrl: string;
  publicUrl: string | null;
  feedbackPublicUrl: string | null;
  viewCount: number;
  isActive: boolean;
  createdByName: string | null;
  createdAt: string;
  updatedAt: string;
};

export type ParticipantListResult = {
  items: Participant[];
  total: number;
  limit: number;
  offset: number;
};

export type CreateParticipantInput = {
  fullName: string;
  companyName: string;
  visitDate: string;
  participantInfo?: string;
  thankYouMessage?: string;
  photo: File;
};
