from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    KAFKA_BROKER: str
    MINING_JOBS_TOPIC: str = "mining_jobs"
    FOUND_BLOCKS_TOPIC: str = "found_blocks"
    NODE_NUMBER: str
    DIFFICULTY: int = 2

    @property
    def MINER_ID(self) -> str:
        return f"miner{self.NODE_NUMBER}"

settings = Settings()
