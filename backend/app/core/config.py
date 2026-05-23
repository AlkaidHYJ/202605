from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "企业智能数据洞察与数字员工协同平台"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "change-me-in-production-use-env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "edata"
    MYSQL_PASSWORD: str = "edata123"
    MYSQL_DATABASE: str = "edata_platform"

    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    ELASTICSEARCH_HOST: str = "http://127.0.0.1:9200"
    ELASTICSEARCH_INDEX_MESSAGES: str = "im_messages"

    NL2SQL_TIMEOUT_SECONDS: int = 10
    NL2SQL_MAX_ROWS: int = 1000
    IM_CONTEXT_ROUNDS: int = 20

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
