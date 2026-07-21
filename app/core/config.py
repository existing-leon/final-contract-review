"""集中配置：基于 pydantic-settings 从环境变量 / .env 读取。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 应用
    APP_NAME: str = "contract-review"
    APP_ENV: str = "dev"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # 数据库
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "contract_review"

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # 审批系统接入
    APPROVAL_BASE_URL: str = "https://approval.example.com"
    APPROVAL_API_KEY: str = ""

    # JWT 认证
    SECRET_KEY: str = "change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_MINUTES: int = 60 * 24  # access token 有效期（分钟），默认 24 小时

    # 附件本地存储
    ATTACHMENT_DIR: str = "./storage"

    # 示例合同目录（mock 附件的真实 PDF 来源）
    SAMPLES_DIR: str = "./samples"

    # LLM（可选，用于条款理解与摘要生成）
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""

    # LLM 请求超时（秒）
    LLM_TIMEOUT: int = 60
    # LLM 连接：False=忽略系统/环境代理直连（dashscope 等国内服务推荐，避免代理导致 SSL EOF）
    LLM_TRUST_ENV: bool = False
    # LLM 调用失败重试次数
    LLM_MAX_RETRIES: int = 3

    # 演示模式：True 时审批系统接口返回 mock 数据（开箱可演示）；对接真实审批系统时置 False
    MOCK_APPROVAL: bool = True

    # OCR 版面分析：True 时扫描件优先用 PaddleOCR PP-Structure 做版面+表格还原
    OCR_USE_LAYOUT: bool = True

    # OCR 提供方：local=本地 PaddleOCR（默认，数据不出本机，推荐生产）；
    #             baidu_api=百度智能云文字识别 API（过渡方案，数据会上传百度云）
    OCR_PROVIDER: str = "local"
    # OCR 网络：False=忽略系统/环境代理直连（百度云为国内服务）
    OCR_TRUST_ENV: bool = False

    # 百度智能云文字识别 OCR（OCR_PROVIDER=baidu_api 时使用）
    BAIDU_OCR_API_KEY: str = ""
    BAIDU_OCR_SECRET_KEY: str = ""
    BAIDU_OCR_GENERAL_URL: str = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
    BAIDU_OCR_TABLE_URL: str = "https://aip.baidubce.com/rest/2.0/ocr/v1/table"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
