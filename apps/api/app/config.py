"""Central config. Reads .env. Every integration is optional; absence => mock mode."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    # core
    database_url: str = "sqlite:///./.fitlens.db"
    environment: str = "development"
    api_port: int = 8000
    web_origin: str = "http://localhost:3000"

    # vector
    vector_provider: str = "local"  # local|pinecone|weaviate
    pinecone_api_key: str = ""
    pinecone_index: str = "fitlens"
    weaviate_url: str = ""
    weaviate_api_key: str = ""

    # llm
    llm_provider: str = "local"  # local|openai|anthropic|gemini
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""

    # ATS / VMS
    jobdiva_client_id: str = ""
    jobdiva_username: str = ""
    jobdiva_password: str = ""
    bullhorn_client_id: str = ""
    bullhorn_client_secret: str = ""
    bullhorn_username: str = ""
    bullhorn_password: str = ""
    ceipal_api_key: str = ""
    ceipal_email: str = ""
    ceipal_password: str = ""

    # job boards
    dice_api_key: str = ""
    indeed_publisher_id: str = ""
    monster_api_key: str = ""
    linkedin_access_token: str = ""

    # comms
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    ms_graph_tenant_id: str = ""
    ms_graph_client_id: str = ""
    ms_graph_client_secret: str = ""

    # auth
    auth_provider: str = "dev"  # dev|azuread|okta
    azure_ad_tenant_id: str = ""
    azure_ad_client_id: str = ""
    okta_domain: str = ""
    okta_client_id: str = ""
    # RBAC / dev token signing (HS256). Override JWT_SECRET in prod.
    jwt_secret: str = "dev-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60
    auth_enforced: bool = False  # when False, requests without a token act as 'admin' (dev)

    # database pooling (ignored by SQLite)
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_pre_ping: bool = True

    # vector (pgvector)
    pgvector_table: str = "embeddings"

    # observability
    log_level: str = "INFO"
    log_json: bool = False  # True => one JSON object per log line (prod)
    request_id_header: str = "X-Request-ID"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
