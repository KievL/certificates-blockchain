from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    KAFKA_BROKER: str
    NODE_NUMBER: str
    TOTAL_NODES: int
    TRANSACTIONS_TOPIC: str = "transactions"
    MINING_JOBS_TOPIC: str = "mining_jobs"
    FOUND_BLOCKS_TOPIC: str = "found_blocks"
    BATCH_SIZE: int = 3
    MINING_TIMEOUT_SECONDS: float = 30.0
    JITTER_MAX_SECONDS: float = 5.0

    @property
    def NODE_ID(self) -> str:
        return f"node{self.NODE_NUMBER}"


settings = Settings()
