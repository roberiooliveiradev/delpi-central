-- Bootstrap (run ONCE as a PostgreSQL superuser, e.g. via psql against the
-- plugins Postgres instance). Creates the dedicated database and the two
-- least-privilege roles frozen in SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE.
--
--   psql -h <host> -U postgres -f bootstrap.sql
--
-- Passwords must be supplied via the psql session, e.g.:
--   psql -v app_password='...' -v admin_password='...' -f bootstrap.sql
-- or edit the CREATE ROLE lines locally and never commit real secrets.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bpmn_modeler_app') THEN
        CREATE ROLE bpmn_modeler_app LOGIN PASSWORD :'app_password';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bpmn_modeler_admin') THEN
        CREATE ROLE bpmn_modeler_admin LOGIN PASSWORD :'admin_password';
    END IF;
END
$$;

SELECT 'CREATE DATABASE bpmn_modeler OWNER bpmn_modeler_admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'bpmn_modeler')
\gexec

-- Connect to bpmn_modeler afterwards and revoke broad defaults.
\connect bpmn_modeler

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO bpmn_modeler_app;
GRANT USAGE, CREATE ON SCHEMA public TO bpmn_modeler_admin;

-- Object-level grants are applied by V001 (tables must exist first).
