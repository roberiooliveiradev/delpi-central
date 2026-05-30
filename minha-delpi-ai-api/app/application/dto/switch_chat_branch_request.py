from dataclasses import dataclass


@dataclass(frozen=True)
class SwitchChatBranchRequest:
    user_id: str
    session_id: str
    anchor_user_message_id: str
