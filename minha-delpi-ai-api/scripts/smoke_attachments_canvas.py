#!/usr/bin/env python3
"""Smoke local — Playbook 05 anexos e lousa (L1, L2, L5, L7, L11, L12)."""

from __future__ import annotations

import sys

from app.application.services.chat_attachment_follow_up_service import (
    ChatAttachmentFollowUpService,
)
from app.application.services.chat_attachment_welcome_service import (
    ChatAttachmentWelcomeService,
)
from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.application.services.chat_canvas_follow_up_service import ChatCanvasFollowUpService
from app.domain.services.chat_canvas_transform_service import ChatCanvasTransformService
from tests.fixtures.attachments_canvas_cases import ATTACHMENTS_CANVAS_CASES


def main() -> int:
    failed = 0

    for case in ATTACHMENTS_CANVAS_CASES:
        case_id = case["id"]
        kind = case.get("kind")

        if kind == "welcome" or kind == "large_file" or kind == "unreadable":
            answer = ChatAttachmentWelcomeService.build_direct_answer(
                attachments=case.get("attachments"),
            )

            if not answer or not all(
                token.lower() in answer.lower() for token in case["expect_substrings"]
            ):
                print(f"FAIL {case_id} welcome", file=sys.stderr)
                failed += 1
                continue

            print(f"OK {case_id} welcome")

        elif kind == "follow_up":
            metadata: dict = {}
            ChatAttachmentFollowUpService.attach_to_assistant_metadata(
                metadata,
                had_attachments=True,
                attachments=[{"original_filename": "dados.xlsx", "status": "indexed"}],
            )
            labels = [
                item["label"]
                for item in metadata.get("attachmentFollowUpSuggestions") or []
            ]

            if not all(label in labels for label in case["expect_labels"]):
                print(f"FAIL {case_id} chips {labels}", file=sys.stderr)
                failed += 1
                continue

            print(f"OK {case_id} chips")

        elif kind in {"canvas_copy", "attachment_to_canvas", "canvas_append", "canvas_transform"}:
            action = ChatCanvasContentService.resolve(
                case["message"],
                case["previous_messages"],
                {"capabilities": {"canvas": True}},
            )

            if not action or not action.open_payload:
                print(f"FAIL {case_id} canvas", file=sys.stderr)
                failed += 1
                continue

            for token in case.get("expect_substrings") or ():
                if token not in action.open_payload.markdown:
                    print(f"FAIL {case_id} missing {token}", file=sys.stderr)
                    failed += 1
                    break
            else:
                for token in case.get("expect_markdown_substrings") or ():
                    if token not in action.open_payload.markdown:
                        print(f"FAIL {case_id} markdown missing {token}", file=sys.stderr)
                        failed += 1
                        break
                else:
                    print(f"OK {case_id} canvas")

        elif kind == "canvas_ambiguity":
            action = ChatCanvasContentService.resolve(
                case["message"],
                case["previous_messages"],
                {"capabilities": {"canvas": True}},
            )

            if not action or action.open_payload is not None:
                print(f"FAIL {case_id} ambiguity", file=sys.stderr)
                failed += 1
                continue

            print(f"OK {case_id} ambiguity")

    metadata: dict = {}
    ChatCanvasFollowUpService.attach_to_assistant_metadata(
        metadata,
        workspace_context={"capabilities": {"canvas": True}},
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {"canvasOpen": {"title": "T", "markdown": "# T\n\nx"}},
            }
        ],
    )

    if not metadata.get("canvasFollowUpSuggestions"):
        print("FAIL canvas follow-up chips", file=sys.stderr)
        failed += 1
    else:
        print("OK canvas follow-up chips")

    checklist, _ = ChatCanvasTransformService.transform("item a\nitem b", "checklist")

    if "- [ ]" not in checklist:
        print("FAIL canvas transform checklist", file=sys.stderr)
        failed += 1
    else:
        print("OK canvas transform checklist")

    if failed:
        return 1

    print("Smoke attachments canvas: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
