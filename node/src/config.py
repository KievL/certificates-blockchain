from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    KAFKA_BROKER: str
    NODE_NUMBER: str
    TOTAL_NODES: int
    TRANSACTIONS_TOPIC: str
    BLOCKS_TOPIC: str

    @property
    def NODE_ID(self) -> str:
        return f"node{self.NODE_NUMBER}"


settings = Settings()
