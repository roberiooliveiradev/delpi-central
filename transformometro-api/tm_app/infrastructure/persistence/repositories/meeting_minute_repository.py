from __future__ import annotations

import json
from typing import Any

from psycopg.types.json import Jsonb

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

_S = "transformometro"


class MeetingMinuteRepository(PluginBaseRepository):
    def _audit(self, cur, *, minute_id: str | None, unit_code: str, entity_type: str,
               entity_id: str | None, action: str, actor_user_id: str | None,
               before: Any = None, after: Any = None) -> None:
        cur.execute(
            f"""INSERT INTO {_S}.tm_meeting_minute_audit_logs
                (minute_id,unit_code,entity_type,entity_id,action,actor_user_id,before_data,after_data)
                VALUES (%s::uuid,%s,%s,%s::uuid,%s,%s::uuid,%s,%s)""",
            (minute_id, unit_code, entity_type, entity_id, action, actor_user_id,
             Jsonb(json.loads(json.dumps(before, default=str))) if before is not None else None,
             Jsonb(json.loads(json.dumps(after, default=str))) if after is not None else None),
        )

    def list_minutes(self, *, unit_codes: list[str], status: str | None = None,
                     meeting_type: str | None = None, q: str | None = None,
                     pending_for_user_id: str | None = None, date_from: str | None = None,
                     date_to: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        clauses, params = ["m.deleted_at IS NULL", "m.unit_code = ANY(%s)"], [unit_codes]
        for column, value in (
            ("m.status =", status),
            ("m.meeting_type =", meeting_type),
            ("m.meeting_date >=", date_from),
            ("m.meeting_date <=", date_to),
        ):
            if value:
                clauses.append(f"{column} %s")
                params.append(value)
        if q:
            clauses.append("(m.title ILIKE %s OR m.minute_number ILIKE %s)")
            params += [f"%{q}%", f"%{q}%"]
        if pending_for_user_id:
            clauses.append("""EXISTS (SELECT 1 FROM transformometro.tm_meeting_minute_signers s
                WHERE s.minute_id=m.id AND s.user_id=%s::uuid AND s.version_id=m.current_version_id
                AND s.status IN ('pending','viewed'))""")
            params.append(pending_for_user_id)
        where = " AND ".join(clauses)
        total = int((self.fetch_one(f"SELECT COUNT(*) AS total FROM {_S}.tm_meeting_minutes m WHERE {where}", tuple(params)) or {}).get("total") or 0)
        rows = self.fetch_all(f"""SELECT m.*,
            (SELECT COUNT(*) FROM {_S}.tm_meeting_minute_signers s WHERE s.minute_id=m.id AND s.version_id=m.current_version_id AND s.status='signed') AS signatures_done,
            (SELECT COUNT(*) FROM {_S}.tm_meeting_minute_signers s WHERE s.minute_id=m.id AND s.version_id=m.current_version_id AND s.status IN ('pending','viewed')) AS signatures_pending
            FROM {_S}.tm_meeting_minutes m WHERE {where}
            ORDER BY m.meeting_date DESC,m.updated_at DESC LIMIT %s OFFSET %s""", tuple(params + [limit, offset]))
        return rows, total

    def get_minute(self, minute_id: str) -> dict[str, Any] | None:
        return self.fetch_one(f"SELECT * FROM {_S}.tm_meeting_minutes WHERE id=%s::uuid AND deleted_at IS NULL", (minute_id,))

    def create_minute(self, **data: Any) -> dict[str, Any]:
        conn = self._connection
        try:
            with conn.cursor() as cur:
                year = str(data["meeting_date"])[:4]
                cur.execute(f"""SELECT minute_number FROM {_S}.tm_meeting_minutes
                    WHERE unit_code=%s AND minute_number LIKE %s AND deleted_at IS NULL
                    ORDER BY minute_number DESC LIMIT 1 FOR UPDATE""", (data["unit_code"], f"{year}/%"))
                last = cur.fetchone()
                seq = int(str(last["minute_number"]).split("/", 1)[1]) if last else 0
                number = f"{year}/{seq + 1:03d}"
                cur.execute(f"""INSERT INTO {_S}.tm_meeting_minutes
                    (unit_code,title,minute_number,meeting_type,meeting_date,start_time,end_time,location,
                     responsible_user_id,responsible_name,chair_name,secretary_name,status,created_by_user_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::uuid,%s,%s,%s,'draft',%s::uuid) RETURNING *""",
                    (data["unit_code"],data["title"],number,data["meeting_type"],data["meeting_date"],data.get("start_time"),data.get("end_time"),data.get("location"),data.get("responsible_user_id"),data.get("responsible_name"),data.get("chair_name"),data.get("secretary_name"),data["created_by_user_id"]))
                minute = dict(cur.fetchone())
                cur.execute(f"""INSERT INTO {_S}.tm_meeting_minute_versions
                    (minute_id,unit_code,version_number,title,meeting_type,meeting_date,start_time,end_time,location,agenda_html,body_html,decisions_html,pending_html,observations_html,content_hash,change_reason,created_by_user_id)
                    VALUES (%s,%s,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Criação inicial',%s::uuid) RETURNING *""",
                    (minute["id"],data["unit_code"],data["title"],data["meeting_type"],data["meeting_date"],data.get("start_time"),data.get("end_time"),data.get("location"),data["agenda_html"],data["body_html"],data["decisions_html"],data["pending_html"],data["observations_html"],data["content_hash"],data["created_by_user_id"]))
                version = dict(cur.fetchone())
                cur.execute(f"UPDATE {_S}.tm_meeting_minutes SET current_version_id=%s,updated_at=NOW() WHERE id=%s RETURNING *",(version["id"],minute["id"]))
                minute = dict(cur.fetchone())
                self._audit(cur, minute_id=str(minute["id"]), unit_code=data["unit_code"], entity_type="meeting_minute", entity_id=str(minute["id"]), action="create", actor_user_id=data["created_by_user_id"], after=minute)
            conn.commit()
            return minute
        except Exception:
            conn.rollback()
            raise

    def update_minute_draft(self, minute_id: str, fields: dict[str, Any], actor_user_id: str) -> dict[str, Any]:
        allowed = {"title","meeting_type","meeting_date","start_time","end_time","location","responsible_user_id","responsible_name","chair_name","secretary_name"}
        fields = {k:v for k,v in fields.items() if k in allowed}
        if not fields: return self.get_minute(minute_id) or (_ for _ in ()).throw(LookupError("Ata não encontrada."))
        sets = [f"{key}=%s{'::uuid' if key == 'responsible_user_id' else ''}" for key in fields]
        row = self.execute_returning_one(f"""UPDATE {_S}.tm_meeting_minutes SET {','.join(sets)},updated_at=NOW()
            WHERE id=%s::uuid AND deleted_at IS NULL RETURNING *""", tuple(fields.values())+(minute_id,))
        if not row: raise LookupError("Ata não encontrada.")
        return row

    def get_version(self, minute_id: str, version_id: str | None = None) -> dict[str, Any] | None:
        if version_id:
            return self.fetch_one(f"SELECT * FROM {_S}.tm_meeting_minute_versions WHERE id=%s::uuid AND minute_id=%s::uuid",(version_id,minute_id))
        return self.fetch_one(f"""SELECT v.* FROM {_S}.tm_meeting_minute_versions v
            JOIN {_S}.tm_meeting_minutes m ON m.current_version_id=v.id WHERE m.id=%s::uuid""",(minute_id,))

    def list_versions(self, minute_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(f"""SELECT id,minute_id,version_number,content_hash,change_reason,created_by_user_id,created_at,title
            FROM {_S}.tm_meeting_minute_versions WHERE minute_id=%s::uuid ORDER BY version_number DESC""",(minute_id,))

    def update_current_version_content(self, *, minute_id: str, actor_user_id: str, **data: Any) -> dict[str, Any]:
        minute = self.get_minute(minute_id)
        if not minute or not minute.get("current_version_id"): raise LookupError("Ata não encontrada.")
        row = self.execute_returning_one(f"""UPDATE {_S}.tm_meeting_minute_versions SET
            agenda_html=%s,body_html=%s,decisions_html=%s,pending_html=%s,observations_html=%s,content_hash=%s
            WHERE id=%s RETURNING *""",(data["agenda_html"],data["body_html"],data["decisions_html"],data["pending_html"],data["observations_html"],data["content_hash"],minute["current_version_id"]))
        if not row: raise LookupError("Versão atual não encontrada.")
        return row

    def create_new_version(self, *, minute_id: str, change_reason: str, agenda_html: str, body_html: str, decisions_html: str, pending_html: str, observations_html: str, content_hash: str, actor_user_id: str) -> dict[str, Any]:
        conn=self._connection
        try:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {_S}.tm_meeting_minutes WHERE id=%s::uuid AND deleted_at IS NULL FOR UPDATE",(minute_id,))
                minute=dict(cur.fetchone() or {})
                if not minute: raise LookupError("Ata não encontrada.")
                cur.execute(f"UPDATE {_S}.tm_meeting_minute_signers SET status='invalidated',updated_at=NOW() WHERE minute_id=%s AND version_id=%s AND status IN ('pending','viewed','signed')",(minute["id"],minute["current_version_id"]))
                # Consome convites abertos da ata — links antigos não devem parecer "elegíveis".
                cur.execute(
                    f"""UPDATE {_S}.tm_meeting_minute_sign_invites
                    SET consumed_at=COALESCE(consumed_at,NOW())
                    WHERE minute_id=%s::uuid AND consumed_at IS NULL""",
                    (minute["id"],),
                )
                cur.execute(f"""INSERT INTO {_S}.tm_meeting_minute_versions
                    (minute_id,unit_code,version_number,title,meeting_type,meeting_date,start_time,end_time,location,agenda_html,body_html,decisions_html,pending_html,observations_html,content_hash,change_reason,created_by_user_id)
                    SELECT %s,unit_code,COALESCE(MAX(version_number),0)+1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::uuid
                    FROM {_S}.tm_meeting_minute_versions WHERE minute_id=%s GROUP BY unit_code RETURNING *""",(minute_id,minute["title"],minute["meeting_type"],minute["meeting_date"],minute["start_time"],minute["end_time"],minute["location"],agenda_html,body_html,decisions_html,pending_html,observations_html,content_hash,change_reason,actor_user_id,minute_id))
                version=dict(cur.fetchone())
                cur.execute(f"UPDATE {_S}.tm_meeting_minutes SET current_version_id=%s,status='in_review',submitted_for_signature_at=NULL,updated_at=NOW() WHERE id=%s RETURNING *",(version["id"],minute_id))
                updated=dict(cur.fetchone())
            conn.commit(); return {"minute":updated,"version":version}
        except Exception: conn.rollback(); raise

    def replace_participants(self, minute_id: str, unit_code: str, participants: list[dict[str, Any]], actor_user_id: str) -> list[dict[str, Any]]:
        conn=self._connection
        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {_S}.tm_meeting_minute_participants WHERE minute_id=%s::uuid",(minute_id,))
                rows=[]
                for index,item in enumerate(participants):
                    cur.execute(f"""INSERT INTO {_S}.tm_meeting_minute_participants
                    (minute_id,unit_code,user_id,display_name,role_in_meeting,presence,is_external,must_sign,sort_order)
                    VALUES (%s::uuid,%s,CAST(%s AS uuid),%s,%s,%s,%s,%s,%s) RETURNING *""",
                    (minute_id, unit_code, item.get("user_id") or None, item["display_name"],
                     item.get("role_in_meeting") or "other", item.get("presence") or "present",
                     bool(item.get("is_external")), bool(item.get("must_sign")),
                     item.get("sort_order", index)))
                    rows.append(dict(cur.fetchone()))
            conn.commit(); return rows
        except Exception: conn.rollback(); raise

    def list_participants(self, minute_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(f"SELECT * FROM {_S}.tm_meeting_minute_participants WHERE minute_id=%s::uuid ORDER BY sort_order,created_at",(minute_id,))

    def replace_signers(self, *, minute_id: str, version_id: str, unit_code: str, signers: list[dict[str, Any]], actor_user_id: str) -> list[dict[str, Any]]:
        conn=self._connection
        try:
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {_S}.tm_meeting_minute_signers WHERE minute_id=%s::uuid AND version_id=%s::uuid",(minute_id,version_id))
                rows=[]
                for index,item in enumerate(signers):
                    user_id = item.get("user_id")
                    user_id = str(user_id).strip() if user_id else None
                    invite_email = str(item.get("invite_email") or "").strip() or None
                    cur.execute(f"""INSERT INTO {_S}.tm_meeting_minute_signers
                    (minute_id,version_id,unit_code,user_id,invite_email,display_name,sign_order,status)
                    VALUES (%s::uuid,%s::uuid,%s,%s::uuid,%s,%s,%s,'pending') RETURNING *""",(
                        minute_id,version_id,unit_code,user_id,invite_email,item["display_name"],item.get("sign_order",index+1),
                    ))
                    rows.append(dict(cur.fetchone()))
            conn.commit(); return rows
        except Exception: conn.rollback(); raise

    def invalidate_open_invites(self, *, signer_id: str) -> int:
        conn = self._connection
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""UPDATE {_S}.tm_meeting_minute_sign_invites
                    SET consumed_at=NOW()
                    WHERE signer_id=%s::uuid AND consumed_at IS NULL""",
                    (signer_id,),
                )
                count = cur.rowcount
            conn.commit()
            return int(count or 0)
        except Exception:
            conn.rollback()
            raise

    def create_invite(
        self,
        *,
        signer_id: str,
        minute_id: str,
        unit_code: str,
        token_hash: str,
        expires_at: Any,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            f"""INSERT INTO {_S}.tm_meeting_minute_sign_invites
            (signer_id,minute_id,unit_code,token_hash,expires_at)
            VALUES (%s::uuid,%s::uuid,%s,%s,%s) RETURNING *""",
            (signer_id, minute_id, unit_code, token_hash, expires_at),
        )
        if not row:
            raise RuntimeError("Falha ao criar convite de assinatura.")
        return row

    def get_invite_by_token_hash(self, token_hash: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT * FROM {_S}.tm_meeting_minute_sign_invites WHERE token_hash=%s",
            (token_hash,),
        )

    def consume_invite(self, invite_id: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""UPDATE {_S}.tm_meeting_minute_sign_invites
            SET consumed_at=COALESCE(consumed_at,NOW())
            WHERE id=%s::uuid RETURNING *""",
            (invite_id,),
        )

    def rebind_invite_signer(self, *, invite_id: str, signer_id: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            f"""UPDATE {_S}.tm_meeting_minute_sign_invites
            SET signer_id=%s::uuid
            WHERE id=%s::uuid AND consumed_at IS NULL
            RETURNING *""",
            (signer_id, invite_id),
        )

    def find_eligible_signer_match(
        self,
        *,
        minute_id: str,
        user_id: str | None,
        invite_email: str | None,
    ) -> dict[str, Any] | None:
        """Signatário elegível na versão atual (mesmo user_id ou e-mail do convite)."""
        uid = str(user_id or "").strip() or None
        email = str(invite_email or "").strip().lower() or None
        if not uid and not email:
            return None
        if uid:
            row = self.fetch_one(
                f"""SELECT s.* FROM {_S}.tm_meeting_minute_signers s
                JOIN {_S}.tm_meeting_minutes m ON m.id=s.minute_id
                WHERE s.minute_id=%s::uuid
                  AND s.version_id=m.current_version_id
                  AND s.status IN ('pending','viewed')
                  AND s.user_id=%s::uuid
                ORDER BY s.sign_order
                LIMIT 1""",
                (minute_id, uid),
            )
            if row:
                return row
        if email:
            return self.fetch_one(
                f"""SELECT s.* FROM {_S}.tm_meeting_minute_signers s
                JOIN {_S}.tm_meeting_minutes m ON m.id=s.minute_id
                WHERE s.minute_id=%s::uuid
                  AND s.version_id=m.current_version_id
                  AND s.status IN ('pending','viewed')
                  AND LOWER(TRIM(COALESCE(s.invite_email,'')))=%s
                ORDER BY s.sign_order
                LIMIT 1""",
                (minute_id, email),
            )
        return None

    def get_signer(self, signer_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT * FROM {_S}.tm_meeting_minute_signers WHERE id=%s::uuid",
            (signer_id,),
        )

    def get_minute(self, minute_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"SELECT * FROM {_S}.tm_meeting_minutes WHERE id=%s::uuid AND deleted_at IS NULL",
            (minute_id,),
        )

    def list_signers(self, minute_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(f"""SELECT s.* FROM {_S}.tm_meeting_minute_signers s JOIN {_S}.tm_meeting_minutes m ON m.id=s.minute_id
            WHERE s.minute_id=%s::uuid AND s.version_id=m.current_version_id ORDER BY s.sign_order""",(minute_id,))

    def get_signer_for_user(self, minute_id: str, user_id: str) -> dict[str, Any] | None:
        return self.fetch_one(f"""SELECT s.* FROM {_S}.tm_meeting_minute_signers s JOIN {_S}.tm_meeting_minutes m ON m.id=s.minute_id
            WHERE s.minute_id=%s::uuid AND s.user_id=%s::uuid AND s.version_id=m.current_version_id""",(minute_id,user_id))

    def mark_signer_viewed(self, signer_id: str) -> dict[str, Any] | None:
        return self.execute_returning_one(f"""UPDATE {_S}.tm_meeting_minute_signers
            SET status=CASE WHEN status='pending' THEN 'viewed' ELSE status END,viewed_at=COALESCE(viewed_at,NOW()),updated_at=NOW()
            WHERE id=%s::uuid RETURNING *""",(signer_id,))

    def set_status(self, *, minute_id: str, status: str, actor_user_id: str, action: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        extra=extra or {}; additions=""; params: list[Any]=[status]
        if status=="awaiting_signatures": additions+=",submitted_for_signature_at=NOW()"
        if status=="finalized": additions+=",finalized_at=NOW(),finalized_by_user_id=%s::uuid"; params.append(actor_user_id)
        if status=="cancelled": additions+=",cancelled_at=NOW(),cancelled_by_user_id=%s::uuid,cancel_reason=%s"; params += [actor_user_id,extra.get("cancel_reason")]
        for key in ("final_pdf_path","final_content_hash","validation_code"):
            if key in extra: additions+=f",{key}=%s"; params.append(extra[key])
        row=self.execute_returning_one(f"UPDATE {_S}.tm_meeting_minutes SET status=%s,updated_at=NOW(){additions} WHERE id=%s::uuid AND deleted_at IS NULL RETURNING *",tuple(params+[minute_id]))
        if not row: raise LookupError("Ata não encontrada.")
        return row

    def register_signature(self, *, minute_id: str, version_id: str, signer_id: str, unit_code: str, user_id: str | None, display_name_confirmed: str, content_hash: str, image_path: str, terms_accepted: bool, client_ip: str | None, user_agent: str | None, session_id: str | None, idempotency_key: str | None, actor_user_id: str) -> dict[str, Any]:
        conn=self._connection
        try:
            with conn.cursor() as cur:
                if idempotency_key:
                    cur.execute(f"SELECT * FROM {_S}.tm_meeting_minute_signatures WHERE idempotency_key=%s",(idempotency_key,))
                    if existing:=cur.fetchone(): return {"signature":dict(existing),"duplicate":True}
                cur.execute(f"SELECT * FROM {_S}.tm_meeting_minute_signers WHERE id=%s::uuid FOR UPDATE",(signer_id,)); signer=cur.fetchone()
                if not signer or signer["status"] in {"signed","invalidated","cancelled","refused"}: raise ValueError("Signatário não está elegível para assinar.")
                uid = str(user_id).strip() if user_id else None
                cur.execute(f"""INSERT INTO {_S}.tm_meeting_minute_signatures
                 (minute_id,version_id,signer_id,unit_code,user_id,display_name_confirmed,content_hash,image_path,terms_accepted,client_ip,user_agent,session_id,idempotency_key)
                 VALUES (%s::uuid,%s::uuid,%s::uuid,%s,%s::uuid,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",(minute_id,version_id,signer_id,unit_code,uid,display_name_confirmed,content_hash,image_path,terms_accepted,client_ip,user_agent,session_id,idempotency_key))
                signature=dict(cur.fetchone())
                cur.execute(f"UPDATE {_S}.tm_meeting_minute_signers SET status='signed',signed_at=NOW(),updated_at=NOW() WHERE id=%s::uuid",(signer_id,))
                cur.execute(f"""SELECT COUNT(*) FILTER (WHERE status='signed') AS signed_count,COUNT(*) AS required_count
                    FROM {_S}.tm_meeting_minute_signers WHERE minute_id=%s::uuid AND version_id=%s::uuid AND status NOT IN ('invalidated','cancelled')""",(minute_id,version_id))
                progress=cur.fetchone()
            conn.commit(); return {"signature":signature,"duplicate":False,"signed_count":int(progress["signed_count"]),"required_count":int(progress["required_count"])}
        except Exception: conn.rollback(); raise

    def list_signatures(self, minute_id: str, version_id: str | None = None) -> list[dict[str, Any]]:
        if version_id:
            return self.fetch_all(
                f"""SELECT * FROM {_S}.tm_meeting_minute_signatures
                WHERE minute_id=%s::uuid AND version_id=%s::uuid
                ORDER BY created_at""",
                (minute_id, version_id),
            )
        return self.fetch_all(
            f"""SELECT sig.* FROM {_S}.tm_meeting_minute_signatures sig
            JOIN {_S}.tm_meeting_minutes m ON m.id=sig.minute_id
            WHERE sig.minute_id=%s::uuid AND sig.version_id=m.current_version_id
            ORDER BY sig.created_at""",
            (minute_id,),
        )
    def get_signature(self, minute_id: str, signature_id: str) -> dict[str, Any] | None:
        return self.fetch_one(f"SELECT * FROM {_S}.tm_meeting_minute_signatures WHERE id=%s::uuid AND minute_id=%s::uuid",(signature_id,minute_id))
    def refuse_signature(self, *, minute_id: str, signer_id: str, reason: str, actor_user_id: str, unit_code: str) -> dict[str, Any]:
        row=self.execute_returning_one(f"UPDATE {_S}.tm_meeting_minute_signers SET status='refused',refuse_reason=%s,refused_at=NOW(),updated_at=NOW() WHERE id=%s::uuid AND minute_id=%s::uuid RETURNING *",(reason,signer_id,minute_id))
        if not row: raise LookupError("Signatário não encontrado.")
        return row
    def soft_delete(self, minute_id: str, actor_user_id: str) -> dict[str, Any]:
        row=self.execute_returning_one(f"UPDATE {_S}.tm_meeting_minutes SET deleted_at=NOW(),updated_at=NOW() WHERE id=%s::uuid AND deleted_at IS NULL RETURNING *",(minute_id,))
        if not row: raise LookupError("Ata não encontrada.")
        return row
    def list_audit(self, minute_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(f"SELECT * FROM {_S}.tm_meeting_minute_audit_logs WHERE minute_id=%s::uuid ORDER BY created_at DESC LIMIT 200",(minute_id,))
