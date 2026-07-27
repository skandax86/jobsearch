"""initial schema

Revision ID: 20b0873af571
Revises:
Create Date: 2026-07-26

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20b0873af571"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))

    op.execute(sa.text("""
CREATE TABLE companies (
	name VARCHAR(255) NOT NULL, 
	normalized_name VARCHAR(255) NOT NULL, 
	website VARCHAR(512), 
	industry VARCHAR(128), 
	enrichment JSONB, 
	provenance JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_companies PRIMARY KEY (id)
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_companies_normalized_name ON companies (normalized_name)
"""))

    op.execute(sa.text("""
CREATE TABLE outbox_events (
	aggregate_type VARCHAR(64) NOT NULL, 
	aggregate_id UUID NOT NULL, 
	event_type VARCHAR(128) NOT NULL, 
	payload JSONB NOT NULL, 
	published_at TIMESTAMP WITH TIME ZONE, 
	publish_attempts INTEGER DEFAULT '0' NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_outbox_events PRIMARY KEY (id)
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_outbox_events_unpublished ON outbox_events (created_at) WHERE published_at IS NULL
"""))

    op.execute(sa.text("""
CREATE INDEX ix_outbox_events_aggregate ON outbox_events (aggregate_type, aggregate_id)
"""))

    op.execute(sa.text("""
CREATE TABLE resume_contents (
	schema_version VARCHAR(32) NOT NULL, 
	content JSONB NOT NULL, 
	content_checksum VARCHAR(128) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_resume_contents PRIMARY KEY (id)
)
"""))

    op.execute(sa.text("""
CREATE TABLE resume_templates (
	name VARCHAR(128) NOT NULL, 
	version VARCHAR(32) NOT NULL, 
	format VARCHAR(32) NOT NULL, 
	definition JSONB, 
	definition_object_key VARCHAR(1024), 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_resume_templates PRIMARY KEY (id), 
	CONSTRAINT uq_resume_templates_name_version UNIQUE (name, version)
)
"""))

    op.execute(sa.text("""
CREATE TABLE users (
	email VARCHAR(320) NOT NULL, 
	email_verified_at TIMESTAMP WITH TIME ZONE, 
	password_hash TEXT, 
	display_name VARCHAR(255), 
	status VARCHAR(32) DEFAULT 'active' NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_users PRIMARY KEY (id), 
	CONSTRAINT uq_users_email UNIQUE (email)
)
"""))

    op.execute(sa.text("""
CREATE TABLE audit_events (
	user_id UUID, 
	actor_type VARCHAR(32) NOT NULL, 
	actor_id UUID, 
	action VARCHAR(128) NOT NULL, 
	resource_type VARCHAR(64) NOT NULL, 
	resource_id UUID, 
	metadata JSONB, 
	ip_address INET, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_audit_events PRIMARY KEY (id), 
	CONSTRAINT fk_audit_events_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_audit_events_resource ON audit_events (resource_type, resource_id)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_audit_events_user_created ON audit_events (user_id, created_at)
"""))

    op.execute(sa.text("""
CREATE TABLE candidate_profiles (
	user_id UUID NOT NULL, 
	headline VARCHAR(255), 
	summary TEXT, 
	location VARCHAR(255), 
	work_authorization JSONB, 
	profile_data JSONB, 
	preferences_version INTEGER DEFAULT '1' NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_candidate_profiles PRIMARY KEY (id), 
	CONSTRAINT uq_candidate_profiles_user_id UNIQUE (user_id), 
	CONSTRAINT fk_candidate_profiles_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE TABLE consents (
	user_id UUID NOT NULL, 
	consent_type VARCHAR(64) NOT NULL, 
	version VARCHAR(32) NOT NULL, 
	granted BOOLEAN DEFAULT 'true' NOT NULL, 
	granted_at TIMESTAMP WITH TIME ZONE, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	metadata JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_consents PRIMARY KEY (id), 
	CONSTRAINT fk_consents_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_consents_user_id_consent_type ON consents (user_id, consent_type)
"""))

    op.execute(sa.text("""
CREATE TABLE integration_connections (
	user_id UUID NOT NULL, 
	provider VARCHAR(64) NOT NULL, 
	status VARCHAR(32) DEFAULT 'active' NOT NULL, 
	scopes JSONB, 
	external_account_id VARCHAR(255), 
	credentials_ref VARCHAR(512), 
	last_synced_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_integration_connections PRIMARY KEY (id), 
	CONSTRAINT uq_integration_connections_user_provider UNIQUE (user_id, provider), 
	CONSTRAINT fk_integration_connections_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_integration_connections_user_id_status ON integration_connections (user_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE job_postings (
	company_id UUID, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	location VARCHAR(255), 
	remote_type VARCHAR(64), 
	compensation JSONB, 
	requirements JSONB, 
	status VARCHAR(32) DEFAULT 'discovered' NOT NULL, 
	posted_at TIMESTAMP WITH TIME ZONE, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	canonical_url VARCHAR(2048), 
	embedding VECTOR(1536), 
	embedding_model VARCHAR(128), 
	embedding_model_version VARCHAR(64), 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_job_postings PRIMARY KEY (id), 
	CONSTRAINT fk_job_postings_company_id_companies FOREIGN KEY(company_id) REFERENCES companies (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_job_postings_company_id ON job_postings (company_id)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_job_postings_status_posted_at ON job_postings (status, posted_at)
"""))

    op.execute(sa.text("""
CREATE TABLE sessions (
	user_id UUID NOT NULL, 
	refresh_token_hash VARCHAR(128) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	user_agent TEXT, 
	ip_address INET, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_sessions PRIMARY KEY (id), 
	CONSTRAINT fk_sessions_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_sessions_user_id_expires_at ON sessions (user_id, expires_at)
"""))

    op.execute(sa.text("""
CREATE TABLE workflows (
	user_id UUID NOT NULL, 
	workflow_type VARCHAR(64) NOT NULL, 
	status VARCHAR(32) DEFAULT 'pending' NOT NULL, 
	input JSONB, 
	state JSONB, 
	correlation_id VARCHAR(128), 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_workflows PRIMARY KEY (id), 
	CONSTRAINT fk_workflows_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_workflows_correlation_id ON workflows (correlation_id)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_workflows_user_id_status ON workflows (user_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE automation_policies (
	candidate_profile_id UUID NOT NULL, 
	enabled BOOLEAN DEFAULT 'false' NOT NULL, 
	max_daily_applications INTEGER, 
	require_approval BOOLEAN DEFAULT 'true' NOT NULL, 
	rules JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_automation_policies PRIMARY KEY (id), 
	CONSTRAINT fk_automation_policies_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_automation_policies_profile_enabled ON automation_policies (candidate_profile_id, enabled)
"""))

    op.execute(sa.text("""
CREATE TABLE candidate_facts (
	candidate_profile_id UUID NOT NULL, 
	fact_type VARCHAR(64) NOT NULL, 
	fact_key VARCHAR(128) NOT NULL, 
	fact_value JSONB NOT NULL, 
	source VARCHAR(32) DEFAULT 'user' NOT NULL, 
	confidence FLOAT, 
	verified_at TIMESTAMP WITH TIME ZONE, 
	provenance JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_candidate_facts PRIMARY KEY (id), 
	CONSTRAINT fk_candidate_facts_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_candidate_facts_profile_type ON candidate_facts (candidate_profile_id, fact_type)
"""))

    op.execute(sa.text("""
CREATE TABLE feedback_events (
	user_id UUID NOT NULL, 
	candidate_profile_id UUID NOT NULL, 
	target_type VARCHAR(64) NOT NULL, 
	target_id UUID NOT NULL, 
	action VARCHAR(64) NOT NULL, 
	metadata JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_feedback_events PRIMARY KEY (id), 
	CONSTRAINT fk_feedback_events_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_feedback_events_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_feedback_events_target ON feedback_events (target_type, target_id)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_feedback_events_candidate_created ON feedback_events (candidate_profile_id, created_at)
"""))

    op.execute(sa.text("""
CREATE TABLE job_snapshots (
	job_posting_id UUID NOT NULL, 
	snapshot JSONB NOT NULL, 
	checksum VARCHAR(128) NOT NULL, 
	captured_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_job_snapshots PRIMARY KEY (id), 
	CONSTRAINT fk_job_snapshots_job_posting_id_job_postings FOREIGN KEY(job_posting_id) REFERENCES job_postings (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_job_snapshots_job_posting_id ON job_snapshots (job_posting_id)
"""))

    op.execute(sa.text("""
CREATE TABLE job_sources (
	job_posting_id UUID NOT NULL, 
	provider VARCHAR(64) NOT NULL, 
	external_id VARCHAR(255) NOT NULL, 
	source_url VARCHAR(2048), 
	retrieved_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	raw_payload_object_key VARCHAR(1024), 
	raw_payload JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_job_sources PRIMARY KEY (id), 
	CONSTRAINT uq_job_sources_provider_external_id UNIQUE (provider, external_id), 
	CONSTRAINT fk_job_sources_job_posting_id_job_postings FOREIGN KEY(job_posting_id) REFERENCES job_postings (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_job_sources_job_posting_id ON job_sources (job_posting_id)
"""))

    op.execute(sa.text("""
CREATE TABLE preferences (
	candidate_profile_id UUID NOT NULL, 
	version INTEGER NOT NULL, 
	roles JSONB, 
	locations JSONB, 
	compensation JSONB, 
	remote_policy VARCHAR(64), 
	blocked_companies JSONB, 
	other JSONB, 
	is_active BOOLEAN DEFAULT 'true' NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_preferences PRIMARY KEY (id), 
	CONSTRAINT uq_preferences_profile_version UNIQUE (candidate_profile_id, version), 
	CONSTRAINT fk_preferences_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_preferences_profile_active ON preferences (candidate_profile_id, is_active)
"""))

    op.execute(sa.text("""
CREATE TABLE recommendations (
	candidate_profile_id UUID NOT NULL, 
	kind VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	confidence FLOAT, 
	model_version VARCHAR(64) NOT NULL, 
	status VARCHAR(32) DEFAULT 'active' NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_recommendations PRIMARY KEY (id), 
	CONSTRAINT fk_recommendations_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_recommendations_candidate_kind ON recommendations (candidate_profile_id, kind)
"""))

    op.execute(sa.text("""
CREATE TABLE resumes (
	candidate_profile_id UUID NOT NULL, 
	title VARCHAR(255), 
	status VARCHAR(32) DEFAULT 'uploaded' NOT NULL, 
	active_version_id UUID, 
	source_object_key VARCHAR(1024), 
	source_mime_type VARCHAR(128), 
	source_checksum VARCHAR(128), 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_resumes PRIMARY KEY (id), 
	CONSTRAINT fk_resumes_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_resumes_candidate_profile_id_status ON resumes (candidate_profile_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE workflow_tasks (
	workflow_id UUID NOT NULL, 
	task_type VARCHAR(64) NOT NULL, 
	status VARCHAR(32) DEFAULT 'pending' NOT NULL, 
	payload JSONB, 
	result JSONB, 
	attempt_count INTEGER DEFAULT '0' NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_workflow_tasks PRIMARY KEY (id), 
	CONSTRAINT fk_workflow_tasks_workflow_id_workflows FOREIGN KEY(workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_workflow_tasks_workflow_status ON workflow_tasks (workflow_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE agent_executions (
	workflow_id UUID, 
	workflow_task_id UUID, 
	agent_name VARCHAR(128) NOT NULL, 
	model VARCHAR(128), 
	prompt_version VARCHAR(64), 
	status VARCHAR(32) DEFAULT 'running' NOT NULL, 
	input_ref VARCHAR(512), 
	output_ref VARCHAR(512), 
	token_usage JSONB, 
	error TEXT, 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_agent_executions PRIMARY KEY (id), 
	CONSTRAINT fk_agent_executions_workflow_id_workflows FOREIGN KEY(workflow_id) REFERENCES workflows (id) ON DELETE SET NULL, 
	CONSTRAINT fk_agent_executions_workflow_task_id_workflow_tasks FOREIGN KEY(workflow_task_id) REFERENCES workflow_tasks (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_agent_executions_workflow_id ON agent_executions (workflow_id)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_agent_executions_status_created ON agent_executions (status, created_at)
"""))

    op.execute(sa.text("""
CREATE TABLE resume_versions (
	resume_id UUID NOT NULL, 
	content_id UUID, 
	version_number INTEGER NOT NULL, 
	kind VARCHAR(32) DEFAULT 'source' NOT NULL, 
	status VARCHAR(32) DEFAULT 'draft' NOT NULL, 
	parent_version_id UUID, 
	job_posting_id UUID, 
	provenance JSONB, 
	embedding VECTOR(1536), 
	embedding_model VARCHAR(128), 
	embedding_model_version VARCHAR(64), 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_resume_versions PRIMARY KEY (id), 
	CONSTRAINT uq_resume_versions_resume_number UNIQUE (resume_id, version_number), 
	CONSTRAINT fk_resume_versions_resume_id_resumes FOREIGN KEY(resume_id) REFERENCES resumes (id) ON DELETE CASCADE, 
	CONSTRAINT fk_resume_versions_content_id_resume_contents FOREIGN KEY(content_id) REFERENCES resume_contents (id) ON DELETE SET NULL, 
	CONSTRAINT fk_resume_versions_parent_version_id_resume_versions FOREIGN KEY(parent_version_id) REFERENCES resume_versions (id) ON DELETE SET NULL, 
	CONSTRAINT fk_resume_versions_job_posting_id_job_postings FOREIGN KEY(job_posting_id) REFERENCES job_postings (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_resume_versions_resume_id_status ON resume_versions (resume_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE job_matches (
	candidate_profile_id UUID NOT NULL, 
	job_posting_id UUID NOT NULL, 
	resume_version_id UUID, 
	job_snapshot_id UUID, 
	score FLOAT NOT NULL, 
	confidence FLOAT, 
	explanation JSONB, 
	features JSONB, 
	model_version VARCHAR(64) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_job_matches PRIMARY KEY (id), 
	CONSTRAINT fk_job_matches_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE, 
	CONSTRAINT fk_job_matches_job_posting_id_job_postings FOREIGN KEY(job_posting_id) REFERENCES job_postings (id) ON DELETE CASCADE, 
	CONSTRAINT fk_job_matches_resume_version_id_resume_versions FOREIGN KEY(resume_version_id) REFERENCES resume_versions (id) ON DELETE SET NULL, 
	CONSTRAINT fk_job_matches_job_snapshot_id_job_snapshots FOREIGN KEY(job_snapshot_id) REFERENCES job_snapshots (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_job_matches_job_posting_id ON job_matches (job_posting_id)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_job_matches_candidate_score ON job_matches (candidate_profile_id, score)
"""))

    op.execute(sa.text("""
CREATE TABLE resume_renders (
	resume_version_id UUID NOT NULL, 
	template_id UUID, 
	format VARCHAR(16) NOT NULL, 
	status VARCHAR(32) DEFAULT 'queued' NOT NULL, 
	object_key VARCHAR(1024), 
	checksum VARCHAR(128), 
	mime_type VARCHAR(128), 
	renderer_version VARCHAR(64), 
	template_version VARCHAR(64), 
	validation_report JSONB, 
	page_count INTEGER, 
	error TEXT, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_resume_renders PRIMARY KEY (id), 
	CONSTRAINT fk_resume_renders_resume_version_id_resume_versions FOREIGN KEY(resume_version_id) REFERENCES resume_versions (id) ON DELETE CASCADE, 
	CONSTRAINT fk_resume_renders_template_id_resume_templates FOREIGN KEY(template_id) REFERENCES resume_templates (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_resume_renders_version_status ON resume_renders (resume_version_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE application_packages (
	job_snapshot_id UUID, 
	resume_render_id UUID, 
	job_snapshot JSONB, 
	cover_letter JSONB, 
	answers JSONB, 
	evidence JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_application_packages PRIMARY KEY (id), 
	CONSTRAINT fk_application_packages_job_snapshot_id_job_snapshots FOREIGN KEY(job_snapshot_id) REFERENCES job_snapshots (id) ON DELETE SET NULL, 
	CONSTRAINT fk_application_packages_resume_render_id_resume_renders FOREIGN KEY(resume_render_id) REFERENCES resume_renders (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE TABLE skill_gaps (
	candidate_profile_id UUID NOT NULL, 
	job_posting_id UUID, 
	job_match_id UUID, 
	gaps JSONB NOT NULL, 
	model_version VARCHAR(64) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_skill_gaps PRIMARY KEY (id), 
	CONSTRAINT fk_skill_gaps_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE, 
	CONSTRAINT fk_skill_gaps_job_posting_id_job_postings FOREIGN KEY(job_posting_id) REFERENCES job_postings (id) ON DELETE SET NULL, 
	CONSTRAINT fk_skill_gaps_job_match_id_job_matches FOREIGN KEY(job_match_id) REFERENCES job_matches (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_skill_gaps_candidate_profile_id ON skill_gaps (candidate_profile_id)
"""))

    op.execute(sa.text("""
CREATE TABLE applications (
	candidate_profile_id UUID NOT NULL, 
	job_posting_id UUID NOT NULL, 
	application_package_id UUID, 
	status VARCHAR(32) DEFAULT 'draft' NOT NULL, 
	idempotency_key VARCHAR(128) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_applications PRIMARY KEY (id), 
	CONSTRAINT uq_applications_idempotency_key UNIQUE (idempotency_key), 
	CONSTRAINT fk_applications_candidate_profile_id_candidate_profiles FOREIGN KEY(candidate_profile_id) REFERENCES candidate_profiles (id) ON DELETE CASCADE, 
	CONSTRAINT fk_applications_job_posting_id_job_postings FOREIGN KEY(job_posting_id) REFERENCES job_postings (id) ON DELETE CASCADE, 
	CONSTRAINT fk_applications_application_package_id_application_packages FOREIGN KEY(application_package_id) REFERENCES application_packages (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_applications_candidate_status ON applications (candidate_profile_id, status)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_applications_job_posting_id ON applications (job_posting_id)
"""))

    op.execute(sa.text("""
CREATE TABLE application_attempts (
	application_id UUID NOT NULL, 
	attempt_number INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	provider_confirmation VARCHAR(512), 
	evidence JSONB, 
	error TEXT, 
	started_at TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_application_attempts PRIMARY KEY (id), 
	CONSTRAINT uq_application_attempts_app_number UNIQUE (application_id, attempt_number), 
	CONSTRAINT fk_application_attempts_application_id_applications FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE TABLE approvals (
	user_id UUID NOT NULL, 
	workflow_id UUID, 
	application_id UUID, 
	action_type VARCHAR(64) NOT NULL, 
	status VARCHAR(32) DEFAULT 'pending' NOT NULL, 
	payload JSONB, 
	decided_at TIMESTAMP WITH TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_approvals PRIMARY KEY (id), 
	CONSTRAINT fk_approvals_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	CONSTRAINT fk_approvals_workflow_id_workflows FOREIGN KEY(workflow_id) REFERENCES workflows (id) ON DELETE SET NULL, 
	CONSTRAINT fk_approvals_application_id_applications FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE SET NULL
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_approvals_user_id_status ON approvals (user_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE interviews (
	application_id UUID NOT NULL, 
	scheduled_at TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(32) DEFAULT 'detected' NOT NULL, 
	location_or_link VARCHAR(1024), 
	preparation JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_interviews PRIMARY KEY (id), 
	CONSTRAINT fk_interviews_application_id_applications FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_interviews_application_status ON interviews (application_id, status)
"""))

    op.execute(sa.text("""
CREATE TABLE status_history (
	application_id UUID NOT NULL, 
	from_status VARCHAR(32), 
	to_status VARCHAR(32) NOT NULL, 
	reason TEXT, 
	actor_type VARCHAR(32) DEFAULT 'system' NOT NULL, 
	actor_id UUID, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_status_history PRIMARY KEY (id), 
	CONSTRAINT fk_status_history_application_id_applications FOREIGN KEY(application_id) REFERENCES applications (id) ON DELETE CASCADE
)
"""))

    op.execute(sa.text("""
CREATE INDEX ix_status_history_application_created ON status_history (application_id, created_at)
"""))

    op.create_foreign_key(
        "fk_resumes_active_version_id",
        "resumes",
        "resume_versions",
        ["active_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_resumes_active_version_id", "resumes", type_="foreignkey")
    op.drop_table("status_history")
    op.drop_table("interviews")
    op.drop_table("approvals")
    op.drop_table("application_attempts")
    op.drop_table("applications")
    op.drop_table("skill_gaps")
    op.drop_table("application_packages")
    op.drop_table("resume_renders")
    op.drop_table("job_matches")
    op.drop_table("resume_versions")
    op.drop_table("agent_executions")
    op.drop_table("workflow_tasks")
    op.drop_table("resumes")
    op.drop_table("recommendations")
    op.drop_table("preferences")
    op.drop_table("job_sources")
    op.drop_table("job_snapshots")
    op.drop_table("feedback_events")
    op.drop_table("candidate_facts")
    op.drop_table("automation_policies")
    op.drop_table("workflows")
    op.drop_table("sessions")
    op.drop_table("job_postings")
    op.drop_table("integration_connections")
    op.drop_table("consents")
    op.drop_table("candidate_profiles")
    op.drop_table("audit_events")
    op.drop_table("users")
    op.drop_table("resume_templates")
    op.drop_table("resume_contents")
    op.drop_table("outbox_events")
    op.drop_table("companies")
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector"))
