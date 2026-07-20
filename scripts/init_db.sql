-- 合同审批审查系统 建表脚本（MySQL 8.0，utf8mb4）
-- 用法：mysql -u root -p < scripts/init_db.sql

CREATE DATABASE IF NOT EXISTS contract_review
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE contract_review;

-- 1. 审批任务表
CREATE TABLE IF NOT EXISTS approval_tasks (
  id              BIGINT NOT NULL AUTO_INCREMENT,
  approval_code   VARCHAR(64)  NOT NULL COMMENT '审批编号(去重唯一键)',
  approval_title  VARCHAR(255) DEFAULT NULL COMMENT '审批标题',
  applicant_name  VARCHAR(64)  DEFAULT NULL COMMENT '申请人',
  task_status     VARCHAR(16)  NOT NULL DEFAULT 'pending' COMMENT '任务状态',
  write_status    VARCHAR(16)  NOT NULL DEFAULT 'not_written' COMMENT '回写状态',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_approval_code (approval_code),
  KEY idx_task_status (task_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批任务表';

-- 2. 审批附件表
CREATE TABLE IF NOT EXISTS approval_attachments (
  id              BIGINT NOT NULL AUTO_INCREMENT,
  task_id         BIGINT NOT NULL,
  file_name       VARCHAR(255) DEFAULT NULL,
  file_type       VARCHAR(32)  DEFAULT NULL,
  file_path       VARCHAR(512) DEFAULT NULL,
  file_size       BIGINT       DEFAULT NULL,
  checksum        VARCHAR(128) DEFAULT NULL,
  download_status VARCHAR(16)  NOT NULL DEFAULT 'pending',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_att_task (task_id),
  CONSTRAINT fk_att_task FOREIGN KEY (task_id) REFERENCES approval_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批附件表';

-- 3. 合同解析表
CREATE TABLE IF NOT EXISTS contract_parses (
  id               BIGINT NOT NULL AUTO_INCREMENT,
  task_id          BIGINT NOT NULL,
  basic_info_json  JSON COMMENT '合同基本信息',
  clause_info_json JSON COMMENT '条款信息',
  parse_status     VARCHAR(16) NOT NULL DEFAULT 'pending',
  parse_error      TEXT,
  created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_parse_task (task_id),
  CONSTRAINT fk_parse_task FOREIGN KEY (task_id) REFERENCES approval_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同解析表';

-- 4. 审查规则表
CREATE TABLE IF NOT EXISTS review_rules (
  id              BIGINT NOT NULL AUTO_INCREMENT,
  rule_code       VARCHAR(64)  NOT NULL COMMENT '规则编码',
  rule_name       VARCHAR(128) NOT NULL COMMENT '规则名称',
  risk_level      VARCHAR(16)  NOT NULL DEFAULT 'medium' COMMENT '风险等级',
  rule_status     VARCHAR(16)  NOT NULL DEFAULT 'enabled' COMMENT '启用状态',
  match_mode      VARCHAR(16)  NOT NULL COMMENT '匹配模式',
  match_text      TEXT COMMENT '匹配文本/表达式',
  suggestion_text TEXT COMMENT '处理建议',
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_rule_code (rule_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审查规则表';

-- 5. 规则命中表
CREATE TABLE IF NOT EXISTS rule_hits (
  id               BIGINT NOT NULL AUTO_INCREMENT,
  task_id          BIGINT NOT NULL,
  rule_id          BIGINT NOT NULL,
  evidence_text    TEXT COMMENT '命中证据原文片段',
  evidence_position VARCHAR(128) DEFAULT NULL COMMENT '证据位置',
  hit_status       VARCHAR(16) NOT NULL DEFAULT 'hit',
  created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_hit_task (task_id),
  KEY idx_hit_rule (rule_id),
  CONSTRAINT fk_hit_task FOREIGN KEY (task_id) REFERENCES approval_tasks(id) ON DELETE CASCADE,
  CONSTRAINT fk_hit_rule FOREIGN KEY (rule_id) REFERENCES review_rules(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='规则命中表';

-- 6. 审查结果表
CREATE TABLE IF NOT EXISTS review_results (
  id                  BIGINT NOT NULL AUTO_INCREMENT,
  task_id             BIGINT NOT NULL,
  overall_risk_level  VARCHAR(16) NOT NULL COMMENT '总风险等级',
  summary_text        TEXT COMMENT '中文摘要',
  focus_points_json   JSON COMMENT '审批关注点',
  comment_text        TEXT COMMENT '回写内容',
  created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_result_task (task_id),
  CONSTRAINT fk_result_task FOREIGN KEY (task_id) REFERENCES approval_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审查结果表';

-- 7. 评论回写日志表
CREATE TABLE IF NOT EXISTS comment_logs (
  id                  BIGINT NOT NULL AUTO_INCREMENT,
  task_id             BIGINT NOT NULL,
  write_status        VARCHAR(16) NOT NULL DEFAULT 'not_written',
  write_response_text TEXT,
  created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_clog_task (task_id),
  CONSTRAINT fk_clog_task FOREIGN KEY (task_id) REFERENCES approval_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论回写日志表';

-- 8. 任务日志表
CREATE TABLE IF NOT EXISTS task_logs (
  id          BIGINT NOT NULL AUTO_INCREMENT,
  task_id     BIGINT NOT NULL,
  log_level   VARCHAR(16) NOT NULL DEFAULT 'info',
  log_type    VARCHAR(32) NOT NULL,
  log_content TEXT,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_log_task (task_id),
  CONSTRAINT fk_log_task FOREIGN KEY (task_id) REFERENCES approval_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务日志表';
