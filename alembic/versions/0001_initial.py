"""initial schema: 8 tables

Revision ID: 0001
Revises:
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approval_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("approval_code", sa.String(length=64), nullable=False, comment="审批编号(去重唯一键)"),
        sa.Column("approval_title", sa.String(length=255), nullable=True),
        sa.Column("applicant_name", sa.String(length=64), nullable=True),
        sa.Column("task_status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("write_status", sa.String(length=16), nullable=False, server_default="not_written"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("approval_code", name="uk_approval_code"),
    )
    op.create_index("idx_task_status", "approval_tasks", ["task_status"])

    op.create_table(
        "approval_attachments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_type", sa.String(length=32), nullable=True),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("download_status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["approval_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_att_task", "approval_attachments", ["task_id"])

    op.create_table(
        "contract_parses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("basic_info_json", sa.JSON(), nullable=True),
        sa.Column("clause_info_json", sa.JSON(), nullable=True),
        sa.Column("parse_status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["approval_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", name="uk_parse_task"),
    )

    op.create_table(
        "review_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("rule_code", sa.String(length=64), nullable=False),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False, server_default="medium"),
        sa.Column("rule_status", sa.String(length=16), nullable=False, server_default="enabled"),
        sa.Column("match_mode", sa.String(length=16), nullable=False),
        sa.Column("match_text", sa.Text(), nullable=True),
        sa.Column("suggestion_text", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("rule_code", name="uk_rule_code"),
    )

    op.create_table(
        "rule_hits",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_id", sa.BigInteger(), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("evidence_position", sa.String(length=128), nullable=True),
        sa.Column("hit_status", sa.String(length=16), nullable=False, server_default="hit"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["approval_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["review_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hit_task", "rule_hits", ["task_id"])
    op.create_index("idx_hit_rule", "rule_hits", ["rule_id"])

    op.create_table(
        "review_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("overall_risk_level", sa.String(length=16), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("focus_points_json", sa.JSON(), nullable=True),
        sa.Column("comment_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["approval_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", name="uk_result_task"),
    )

    op.create_table(
        "comment_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("write_status", sa.String(length=16), nullable=False, server_default="not_written"),
        sa.Column("write_response_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["approval_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_clog_task", "comment_logs", ["task_id"])

    op.create_table(
        "task_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.BigInteger(), nullable=False),
        sa.Column("log_level", sa.String(length=16), nullable=False, server_default="info"),
        sa.Column("log_type", sa.String(length=32), nullable=False),
        sa.Column("log_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["approval_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_log_task", "task_logs", ["task_id"])


def downgrade() -> None:
    op.drop_table("task_logs")
    op.drop_table("comment_logs")
    op.drop_table("review_results")
    op.drop_table("rule_hits")
    op.drop_table("review_rules")
    op.drop_table("contract_parses")
    op.drop_table("approval_attachments")
    op.drop_table("approval_tasks")
