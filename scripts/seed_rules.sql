-- 审查规则初始化数据（覆盖 PRD 7.2.2 全部 11 个规则主题）
-- 用法：mysql -u root -p contract_review < scripts/seed_rules.sql
-- 注意：含反斜杠的正则已在 SQL 字面量中用双反斜杠转义（'\\d' 存储为 '\d'）。
--       若担心转义差异，推荐改用 scripts/init_data.py（Python 原始字符串）。

USE contract_review;

INSERT INTO review_rules (rule_code, rule_name, risk_level, rule_status, match_mode, match_text, suggestion_text) VALUES
('R001', '预付款比例过高', 'high',   'enabled', 'threshold', '预付款\\D{0,5}(\\d{1,3})\\s*% > 30',          '预付款比例建议不超过 30%，降低提前付款资金风险。'),
('R002', '付款周期过长',   'medium', 'enabled', 'threshold', '付款.{0,6}?([0-9]{1,3})\\s*天 > 60',          '付款周期建议不超过 60 天，避免账期过长。'),
('R003', '自动续约',       'high',   'enabled', 'keyword',   '自动续约|自动续期|自动延续',                    '谨慎接受自动续约条款，建议改为到期人工确认。'),
('R004', '违约责任',       'high',   'enabled', 'keyword',   '违约金|违约责任',                              '核对违约责任是否对等、违约金比例是否合理。'),
('R005', '管辖地不利',     'medium', 'enabled', 'keyword',   '管辖|仲裁|诉讼',                               '确认管辖/仲裁地是否有利于本方。'),
('R006', '主体信息缺失',   'high',   'enabled', 'absence',   'party_a',                                      '缺少签约主体信息，请补充甲方主体。'),
('R007', '金额缺失',       'high',   'enabled', 'absence',   'amount',                                       '缺少合同金额，请补充金额信息。'),
('R008', '保密条款缺失',   'high',   'enabled', 'absence',   'clause.confidentiality',                       '缺少保密条款，建议补充保密义务约定。'),
('R009', '数据处理条款缺失','medium','enabled', 'absence',   'clause.data',                                  '缺少数据处理条款，建议补充数据合规约定。'),
('R010', '知识产权条款缺失','medium','enabled', 'absence',   'clause.ip',                                    '缺少知识产权条款，建议明确权属归属。'),
('R011', '验收标准缺失',   'medium', 'enabled', 'absence',   'clause.acceptance',                            '缺少验收标准条款，建议补充验收标准与流程。')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
