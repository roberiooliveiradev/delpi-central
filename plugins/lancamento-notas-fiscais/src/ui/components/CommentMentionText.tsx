import { splitCommentMentionSegments } from "../../domain/commentMentions";

type Props = {
  text: string;
  className?: string;
};

/** Renderiza comentário com menções em negrito e sem o "@". */
export function CommentMentionText({ text, className }: Props) {
  const segments = splitCommentMentionSegments(text);

  return (
    <p className={className}>
      {segments.map((segment, index) =>
        segment.type === "mention" ? (
          <strong key={`m-${index}`} className="lnf-comment-mention">
            {segment.value}
          </strong>
        ) : (
          <span key={`t-${index}`}>{segment.value}</span>
        ),
      )}
    </p>
  );
}
