-- ============================================================
-- 用户表建表语句（角色与权限管理）
-- 对应模型：app/models/user.py
-- 对应迁移：alembic/versions/0002_users.py
--
-- 使用方式（任选其一）：
--   1) 命令行：  mysql -u root -p contract_review < scripts/create_users.sql
--   2) 客户端：  Navicat / DBeaver / DataGrip 打开本文件执行
--
-- 建表后创建默认账号：python scripts/init_users.py
--   默认账号：admin / admin123（系统管理员）、legal / legal123（法务审核人）
--
-- 注意：本文件与 alembic 迁移 0002 二选一即可，不要重复执行。
-- ============================================================

CREATE TABLE IF NOT EXISTS `users` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT                              COMMENT '主键',
  `username`      VARCHAR(64)  NOT NULL                                             COMMENT '登录用户名',
  `password_hash` VARCHAR(128) NOT NULL                                             COMMENT '密码哈希（bcrypt）',
  `role`          VARCHAR(16)  NOT NULL DEFAULT 'legal'                             COMMENT '角色：admin=系统管理员 / legal=法务审核人',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP                                  COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP        COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_user_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统登录用户';
