#!/usr/bin/env python3
"""Local-dev recovery: reset the master-realm admin credential to the
infra/.env KEYCLOAK_ADMIN_PASSWORD (PBKDF2-SHA256, KC 27500 iters) and
reset the delpi-realm DEV_PORTAL_* user password to .battery/env.local.
Emits SQL on stdout — pipe to psql. LOCAL ONLY.
"""
import base64
import hashlib
import json
import re
import secrets
import sys


def env_val(path, key):
    for line in open(path):
        m = re.match(rf"^{key}=(.*)$", line.strip())
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None


def kc_cred(password: str):
    salt = secrets.token_bytes(16)
    # KC Pbkdf2PasswordHashProvider: DERIVED_KEY_SIZE = 64 bytes.
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 27500, dklen=64)
    secret = {
        "value": base64.b64encode(h).decode(),
        "salt": base64.b64encode(salt).decode(),
        "additionalParameters": {},
    }
    cred = {
        "hashIterations": 27500,
        "algorithm": "pbkdf2-sha256",
        "additionalParameters": {},
    }
    return json.dumps(secret), json.dumps(cred)


def lit(s: str) -> str:
    return (
        "convert_from(decode('"
        + base64.b64encode(s.encode()).decode()
        + "','base64'),'utf8')"
    )


ADMIN_PW = env_val(sys.argv[1], "KEYCLOAK_ADMIN_PASSWORD")
DEV_USER = env_val(sys.argv[2], "DEV_PORTAL_USERNAME")
DEV_PW = env_val(sys.argv[2], "DEV_PORTAL_PASSWORD")
assert ADMIN_PW and DEV_USER and DEV_PW, "missing env values"

sd, ud = kc_cred(ADMIN_PW)
print(
    "update credential set secret_data="
    + lit(sd)
    + ", credential_data="
    + lit(ud)
    + " where user_id=(select id from user_entity where realm_id="
    "(select id from realm where name='master') and username='admin')"
    " and type='password';"
)

sd2, ud2 = kc_cred(DEV_PW)
print(
    "update credential set secret_data="
    + lit(sd2)
    + ", credential_data="
    + lit(ud2)
    + " where user_id=(select id from user_entity where realm_id="
    "(select id from realm where name='delpi') and username='"
    + DEV_USER
    + "')"
    " and type='password';"
)
