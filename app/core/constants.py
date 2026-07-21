"""系统枚举常量。与后端手册 4.3 对齐。"""


class TaskStatus:
    PENDING = "pending"
    PARSING = "parsing"
    REVIEWING = "reviewing"
    BLOCKED = "blocked"
    DONE = "done"


class WriteStatus:
    NOT_WRITTEN = "not_written"
    WRITING = "writing"
    SUCCESS = "success"
    FAILED = "failed"


class RiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    # 取最高风险时用的排序权重
    ORDER = {"low": 1, "medium": 2, "high": 3}

    @classmethod
    def highest(cls, levels: list[str]) -> str:
        valid = [lv for lv in levels if lv in cls.ORDER]
        if not valid:
            return cls.LOW
        return max(valid, key=lambda lv: cls.ORDER[lv])


class RuleStatus:
    ENABLED = "enabled"
    DISABLED = "disabled"


class ParseStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class DownloadStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class HitStatus:
    HIT = "hit"
    NOT_HIT = "not_hit"
    UNCERTAIN = "uncertain"


class MatchMode:
    KEYWORD = "keyword"
    REGEX = "regex"
    THRESHOLD = "threshold"
    ABSENCE = "absence"


class LogLevel:
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class LogType:
    FETCH = "fetch"
    DOWNLOAD = "download"
    PARSE = "parse"
    REVIEW = "review"
    COMMENT = "comment"
    STATE = "state"


class RoleName:
    """登录用户角色（与 PRD 权限矩阵对齐）。"""

    ADMIN = "admin"  # 系统管理员（运维）
    LEGAL = "legal"  # 法务审核人（业务）
