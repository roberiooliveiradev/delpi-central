export const TABLE_PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

export type PaginationPageItem = number | "ellipsis";

export function buildVisiblePageItems(
  currentPage: number,
  totalPages: number,
  siblingCount = 1,
): PaginationPageItem[] {
  if (totalPages <= 1) {
    return [1];
  }

  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const leftSibling = Math.max(currentPage - siblingCount, 2);
  const rightSibling = Math.min(currentPage + siblingCount, totalPages - 1);
  const showLeftEllipsis = leftSibling > 2;
  const showRightEllipsis = rightSibling < totalPages - 1;

  const items: PaginationPageItem[] = [1];

  if (showLeftEllipsis) {
    items.push("ellipsis");
  } else {
    for (let page = 2; page < leftSibling; page += 1) {
      items.push(page);
    }
  }

  for (let page = leftSibling; page <= rightSibling; page += 1) {
    items.push(page);
  }

  if (showRightEllipsis) {
    items.push("ellipsis");
  } else {
    for (let page = rightSibling + 1; page < totalPages; page += 1) {
      items.push(page);
    }
  }

  items.push(totalPages);

  return items;
}
