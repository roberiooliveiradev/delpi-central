import { uploadAttachment } from "../api/requestsApi";

export type StagedUploadResult = {
  uploaded: number;
  failed: number;
  errors: string[];
};

/** After createRequest: upload staged files; request already exists on partial failure. */
export async function uploadStagedAttachments(
  requestId: string,
  files: File[],
): Promise<StagedUploadResult> {
  let uploaded = 0;
  const errors: string[] = [];
  for (const file of files) {
    try {
      await uploadAttachment(requestId, file, crypto.randomUUID());
      uploaded += 1;
    } catch (err) {
      errors.push(
        err instanceof Error
          ? `${file.name}: ${err.message}`
          : `${file.name}: falha no envio`,
      );
    }
  }
  return { uploaded, failed: errors.length, errors };
}
