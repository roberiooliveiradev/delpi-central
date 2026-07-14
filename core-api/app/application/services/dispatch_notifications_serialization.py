# app/application/services/dispatch_notifications_serialization.py

from datetime import datetime

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest


def request_to_payload_dict(request: DispatchNotificationsRequest) -> dict:
    return {
        "title": request.title,
        "message": request.message,
        "type": request.type,
        "category": request.category,
        "presentation": request.presentation,
        "htmlContent": request.html_content,
        "actionType": request.action_type,
        "actionLabel": request.action_label,
        "actionTarget": request.action_target,
        "icon": request.icon,
        "metadata": request.metadata,
        "expiresAt": request.expires_at.isoformat() + "Z" if request.expires_at else None,
        "broadcast": request.broadcast,
        "userIds": list(request.user_ids),
        "emails": list(request.emails),
        "roleIds": list(request.role_ids),
        "groupIds": list(request.group_ids),
        "permissionCodes": list(request.permission_codes),
        "excludedUserIds": list(request.excluded_user_ids),
        "sourceApp": request.source_app,
    }


def payload_dict_to_request(data: dict) -> DispatchNotificationsRequest:
    expires_at = data.get("expiresAt")
    parsed_expires = None
    if expires_at:
        parsed_expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00")).replace(
            tzinfo=None
        )

    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        metadata = None

    return DispatchNotificationsRequest(
        title=data.get("title"),
        message=data.get("message") or "",
        type=data.get("type") or "info",
        category=data.get("category") or "system",
        presentation=data.get("presentation") or "text",
        html_content=data.get("htmlContent") or data.get("html_content"),
        action_type=data.get("actionType") or data.get("action_type"),
        action_label=data.get("actionLabel") or data.get("action_label"),
        action_target=data.get("actionTarget") or data.get("action_target"),
        icon=data.get("icon"),
        metadata=metadata,
        expires_at=parsed_expires,
        broadcast=bool(data.get("broadcast", False)),
        user_ids=[str(item) for item in (data.get("userIds") or data.get("user_ids") or []) if item],
        emails=[str(item) for item in (data.get("emails") or []) if item],
        role_ids=[str(item) for item in (data.get("roleIds") or data.get("role_ids") or []) if item],
        group_ids=[str(item) for item in (data.get("groupIds") or data.get("group_ids") or []) if item],
        permission_codes=[
            str(item).strip()
            for item in (data.get("permissionCodes") or data.get("permission_codes") or [])
            if item
        ],
        excluded_user_ids=[
            str(item)
            for item in (data.get("excludedUserIds") or data.get("excluded_user_ids") or [])
            if item
        ],
        source_app=data.get("sourceApp") or data.get("source_app"),
    )


def extract_template_id(metadata: dict | None) -> str | None:
    if not metadata:
        return None
    template_id = metadata.get("templateId") or metadata.get("template_id")
    return str(template_id) if template_id else None
