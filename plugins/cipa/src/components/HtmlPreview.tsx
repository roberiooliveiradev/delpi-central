import { isHtmlEmpty } from "../utils/htmlContent";

type Props = {
  html: string;
  emptyLabel: string;
};

export function HtmlPreview({ html, emptyLabel }: Props) {
  if (isHtmlEmpty(html)) {
    return <p className="cipa-review-empty">{emptyLabel}</p>;
  }
  return <div className="cipa-prose" dangerouslySetInnerHTML={{ __html: html }} />;
}
