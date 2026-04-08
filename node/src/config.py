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
    DIFFICULTY: int = 4
    PUBLIC_KEY: str

    @property
    def NODE_ID(self) -> str:
        return f"node{self.NODE_NUMBER}"

    @property
    def NODE_URLS(self) -> list[str]:
        """URLs for all nodes based on TOTAL_NODES."""
        return [f"http://node{i}:8000" for i in range(1, self.TOTAL_NODES + 1)]

    @property
    def PEER_URLS(self) -> list[str]:
        """URLs of other nodes (excluding the current one)."""
        return [url for url in self.NODE_URLS if f"node{self.NODE_NUMBER}" not in url]


settings = Settings()
