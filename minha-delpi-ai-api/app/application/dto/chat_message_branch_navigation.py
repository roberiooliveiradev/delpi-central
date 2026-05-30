from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessageBranchNavigation:
    current_index: int
    total: int
    sibling_ids: list[str]

    def to_dict(self) -> dict:
        return {
            "currentIndex": self.current_index,
            "total": self.total,
            "siblingIds": self.sibling_ids,
        }
