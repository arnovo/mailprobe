-- Vacía tablas de histórico; deja leads y workspace_configs (y usuarios, workspaces, api_keys, webhooks, optouts).
-- Desde la raíz del proyecto (con compose en dev):
--   docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T postgres psql -U postgres -d mailprobe < backend/scripts/truncate_historic_tables.sql

TRUNCATE TABLE job_log_lines RESTART IDENTITY CASCADE;
TRUNCATE TABLE verification_logs RESTART IDENTITY CASCADE;
TRUNCATE TABLE jobs RESTART IDENTITY CASCADE;
TRUNCATE TABLE audit_logs RESTART IDENTITY CASCADE;
TRUNCATE TABLE usage RESTART IDENTITY CASCADE;
TRUNCATE TABLE webhook_deliveries RESTART IDENTITY CASCADE;
