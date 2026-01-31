from typing import Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, HttpUrl, model_validator
from urllib.parse import urlparse


class CookieConfig(BaseModel):
    domain: str = "localhost"
    secure: bool = False  # Set to True in production with HTTPS
    httponly: bool = True  # Prevent JavaScript access
    samesite: Literal["lax", "strict", "none"] = "lax"
    max_age: int = 60 * 60 * 24 * 7  # 7 days in seconds


class GeneralConfig(BaseModel):
    development_mode: bool = True
    install_mode: bool = False
    api_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    site_name: str = "Dunistech Academy"
    site_description: str = "Learning Management System"
    contact_email: str = "admin@dunistech.ng"
    timezone: str = "Africa/Lagos"  # Added timezone
    templates_dir: str = "./app/templates"
    frontend_url: str = 'https:salesnet.ng'


class SecurityConfig(BaseModel):
    auth_jwt_secret_key: str  # REQUIRED (my .env)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24        # 24 hours
    refresh_token_expire_minutes: int = 60 * 24 * 7   # 7 days
    refresh_token_rotate: bool = True
    jwt_secret_key: str = "SUPER_SECRET_KEY_EDET_JAMES"
    password_reset_token_expire_minutes: int = 15     # 15 minutes
    email_verification_token_expire_minutes: int = 60 * 24  # 24 hours
    bcrypt_rounds: int = 12  # Password hashing rounds
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

class OAuthConfig(BaseModel):
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None
    
    # facebook/apple similarly...
    facebook_client_id: str | None = None
    facebook_client_secret: str | None = None
    facebook_redirect_uri: str | None = None
    
    twitter_client_id: str | None = None
    twitter_client_secret: str | None = None
    twitter_redirect_uri: str | None = None


class ChromaDBConfig(BaseModel):
    is_separate_database_enabled: bool = False
    db_host: Optional[str] = None
    persist_directory: str = "./chromadb_data"  # Local storage for embeddings
    collection_name: str = "academy_documents"  # Default collection name


class AIConfig(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None  # For Claude
    google_api_key: Optional[str] = None  # For Gemini
    is_ai_enabled: bool = False
    default_model: str = "gpt-3.5-turbo"  # or "claude-3-sonnet", "gemini-pro"
    embedding_model: str = "text-embedding-ada-002"
    chromadb_config: ChromaDBConfig = ChromaDBConfig()


class S3ApiConfig(BaseModel):
    bucket_name: Optional[str] = None
    endpoint_url: Optional[str] = None
    region: str = "us-east-1"
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    use_ssl: bool = True
    signature_version: str = "s3v4"


class ContentDeliveryConfig(BaseModel):
    type: Literal["filesystem", "s3api", "cloudinary"] = "filesystem"
    filesystem_base_path: str = "./uploads"  # Local storage path
    max_file_size_mb: int = 100  # 100MB max file size
    allowed_file_types: list[str] = ["video/mp4", "image/jpeg", "image/png", "image/gif", "application/pdf", "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    s3api: S3ApiConfig = S3ApiConfig()


class HostingConfig(BaseModel):
    domain: str = "localhost"
    ssl: bool = False
    port: int = 8000
    use_default_org: bool = True
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    allowed_regexp: str = ""
    self_hosted: bool = True
    api_url: str = "http://localhost:8000"  # Full API URL
    frontend_url: str = "http://localhost:3000"  # Frontend URL
    cookie_config: CookieConfig = CookieConfig()
    content_delivery: ContentDeliveryConfig = ContentDeliveryConfig()


# class MailConfig(BaseModel):
#     # Email system configuration
#     system_email_address: str = "no-reply@dunistech.ng"
#     mail_sender_name: str = "Dunistech Academy"
#     mail_sender_email: str = "no-reply@dunistech.ng"
    
#     # Provider selection
#     provider: Literal["smtp", "resend", "sendgrid", "mailgun", "console"] = "smtp"
    
#     # SMTP configuration
#     smtp_host: str = "smtp.gmail.com"
#     smtp_port: int = 587
#     smtp_username: str = ""
#     smtp_password: str = ""
#     smtp_use_tls: bool = True
#     smtp_use_ssl: bool = False
#     smtp_timeout: int = 30  # seconds
    
#     # API-based providers
#     resend_api_key: str = ""
#     sendgrid_api_key: str = ""
#     mailgun_api_key: str = ""
#     mailgun_domain: str = ""
    
#     # Email templates directory
#     templates_dir: str = "./app/templates"
    
#     # Rate limiting
#     emails_per_hour: int = 100  # Max emails per hour
#     retry_attempts: int = 3  # Number of retry attempts
    
#     @field_validator('smtp_port')
#     def validate_smtp_port(cls, v):
#         if not 1 <= v <= 65535:
#             raise ValueError('SMTP port must be between 1 and 65535')
#         return v

from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, field_validator, model_validator


class MailConfig(BaseModel):

    # ------------------------------------------------------------------
    # System metadata
    # ------------------------------------------------------------------
    system_email_address: EmailStr = "no-reply@dunistech.ng"
    mail_sender_name: str = "Dunistech Academy"
    mail_sender_email: EmailStr = "no-reply@dunistech.ng"

    # ------------------------------------------------------------------
    # Provider selection
    # ------------------------------------------------------------------
    provider: Literal["smtp", "resend", "sendgrid", "mailgun", "console"] = "smtp"

    # ------------------------------------------------------------------
    # SMTP configuration
    # ------------------------------------------------------------------
    smtp_host: Optional[str] = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None

    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout: int = 30

    # ------------------------------------------------------------------
    # API providers
    # ------------------------------------------------------------------
    resend_api_key: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    mailgun_api_key: Optional[str] = None
    mailgun_domain: Optional[str] = None

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    templates_dir: str = "./app/templates"

    # ------------------------------------------------------------------
    # Limits & retries
    # ------------------------------------------------------------------
    emails_per_hour: int = 100
    retry_attempts: int = 3

    # ------------------------------------------------------------------
    # Field validators
    # ------------------------------------------------------------------
    @field_validator("smtp_port")
    @classmethod
    def validate_smtp_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("SMTP port must be between 1 and 65535")
        return v

    # ------------------------------------------------------------------
    # Provider validation
    # ------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_provider_requirements(self):
        p = self.provider

        if p == "smtp":
            required = [self.smtp_host, self.smtp_username, self.smtp_password]
        elif p == "resend":
            required = [self.resend_api_key]
        elif p == "sendgrid":
            required = [self.sendgrid_api_key]
        elif p == "mailgun":
            required = [self.mailgun_api_key, self.mailgun_domain]
        elif p == "console":
            required = []   # Dev mode only: log emails to console
        else:
            raise ValueError(f"Unsupported mail provider: {p}")

        if not all(required):
            raise ValueError(f"Incomplete credential configuration for provider '{p}'")

        return self


class DatabaseConfig(BaseModel):
    sql_connection_string: Optional[str] = None
    pool_size: int = 20  # Connection pool size
    max_overflow: int = 40  # Max overflow connections
    pool_recycle: int = 3600  # Recycle connections after 1 hour
    pool_timeout: int = 30  # Timeout for getting connection from pool
    echo: bool = False  # Log SQL queries (enable in development)


class RedisConfig(BaseModel):
    redis_connection_string: Optional[str] = None
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None
    ssl: bool = False
    ssl_cert_reqs: Optional[str] = None  # 'required', 'optional', 'none'
    connection_pool_size: int = 10
    socket_timeout: int = 5  # seconds
    socket_connect_timeout: int = 5  # seconds
    retry_on_timeout: bool = True
    decode_responses: bool = True  # Decode responses to strings
    
    # Cache configuration
    default_ttl: int = 3600  # Default TTL in seconds (1 hour)
    session_ttl: int = 86400  # Session TTL (24 hours)
    rate_limit_ttl: int = 60  # Rate limit TTL (1 minute)
    
    # Sentinel configuration (for high availability)
    use_sentinel: bool = False
    sentinel_nodes: list[dict] = []  # [{"host": "localhost", "port": 26379}]
    sentinel_service_name: str = "mymaster"
    sentinel_password: Optional[str] = None
    
    # # @field_validator('redis_connection_string', pre=True, always=True)
    # @field_validator('redis_connection_string', mode='before')
    # @classmethod
    # def parse_connection_string(cls, v, values):
    #     """Parse Redis connection string and populate individual fields."""
    #     if not v:
    #         return None
        
    #     try:
    #         parsed = urlparse(v)
            
    #         # Handle redis:// and rediss:// (SSL) schemes
    #         if parsed.scheme not in ['redis', 'rediss']:
    #             raise ValueError(f"Invalid Redis URL scheme: {parsed.scheme}")
            
    #         # Update values from connection string
    #         values['host'] = parsed.hostname or 'localhost'
    #         values['port'] = parsed.port or 6379
            
    #         # Parse database number from path (e.g., /0)
    #         if parsed.path:
    #             db_str = parsed.path.lstrip('/')
    #             if db_str:
    #                 values['db'] = int(db_str)
            
    #         # Parse credentials
    #         if parsed.username:
    #             values['username'] = parsed.username
    #         if parsed.password:
    #             values['password'] = parsed.password
            
    #         # Set SSL flag for rediss://
    #         if parsed.scheme == 'rediss':
    #             values['ssl'] = True
            
    #         return v
            
    #     except Exception as e:
    #         raise ValueError(f"Invalid Redis connection string: {v}. Error: {e}")
    

from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from urllib.parse import urlparse


class RedisConfig(BaseModel):
    redis_connection_string: Optional[str] = None
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    username: Optional[str] = None
    ssl: bool = False
    ssl_cert_reqs: Optional[str] = None

    connection_pool_size: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    decode_responses: bool = True

    # Cache configuration
    default_ttl: int = 3600
    session_ttl: int = 86400
    rate_limit_ttl: int = 60

    # Sentinel
    use_sentinel: bool = False
    sentinel_nodes: list[dict] = []
    sentinel_service_name: str = "mymaster"
    sentinel_password: Optional[str] = None

    # ------------------------------------------------------
    # VALIDATE + PARSE CONNECTION STRING
    # ------------------------------------------------------
    @model_validator(mode="before")
    @classmethod
    def parse_connection_string(cls, data: dict):
        """
        Parse redis_connection_string and populate fields safely.
        """
        url = data.get("redis_connection_string")
        # print(f"Parsing Redis connection string: {url}")
        
        if not url:
            return data

        parsed = urlparse(url)

        if parsed.scheme not in ("redis", "rediss"):
            raise ValueError(f"Invalid Redis scheme: {parsed.scheme}")

        data["host"] = parsed.hostname or "localhost"
        data["port"] = parsed.port or 6379
        data["ssl"] = parsed.scheme == "rediss"

        # Database index
        if parsed.path and parsed.path.strip("/"):
            data["db"] = int(parsed.path.strip("/"))

        # Auth
        if parsed.username:
            data["username"] = parsed.username

        if parsed.password:
            data["password"] = parsed.password

        return data

    # ------------------------------------------------------
    # PROPERTIES
    # ------------------------------------------------------
    @property
    def connection_url(self) -> str:
        scheme = "rediss" if self.ssl else "redis"

        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        elif self.password:
            auth = f":{self.password}@"

        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"

    @property
    def connection_kwargs(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "password": self.password,
            "username": self.username,
            "ssl": self.ssl,
            "ssl_cert_reqs": self.ssl_cert_reqs,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "retry_on_timeout": self.retry_on_timeout,
            "decode_responses": self.decode_responses,
        }

    # @property
    # def connection_url(self) -> str:
    #     """Generate connection URL from individual parameters."""
    #     scheme = "rediss" if self.ssl else "redis"
    #     auth = ""
        
    #     if self.username and self.password:
    #         auth = f"{self.username}:{self.password}@"
    #     elif self.password:
    #         auth = f":{self.password}@"
        
    #     return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"
    
    # @property
    # def connection_kwargs(self) -> dict:
    #     """Get connection parameters as dictionary for redis client."""
    #     return {
    #         "host": self.host,
    #         "port": self.port,
    #         "db": self.db,
    #         "password": self.password,
    #         "username": self.username,
    #         "ssl": self.ssl,
    #         "ssl_cert_reqs": self.ssl_cert_reqs,
    #         "socket_timeout": self.socket_timeout,
    #         "socket_connect_timeout": self.socket_connect_timeout,
    #         "retry_on_timeout": self.retry_on_timeout,
    #         "decode_responses": self.decode_responses,
    #     }


    
class StripeConfig(BaseModel):
    secret_key: Optional[str] = None
    publishable_key: Optional[str] = None
    webhook_standard_secret: Optional[str] = None
    webhook_connect_secret: Optional[str] = None
    client_id: Optional[str] = None
    api_version: str = "2023-10-16"  # Stripe API version
    max_network_retries: int = 2
    timeout: int = 30  # seconds


class PaystackConfig(BaseModel):
    secret_key: Optional[str] = None
    public_key: Optional[str] = None
    base_url: str = "https://api.paystack.co"
    callback_url: Optional[str] = None  # For payment verification callbacks
    timeout: int = 30  # seconds


class PaymentsConfig(BaseModel):
    default_provider: Literal["stripe", "paystack", "none"] = "none"
    currency: str = "NGN"  # Nigerian Naira
    stripe: StripeConfig = StripeConfig()
    paystack: PaystackConfig = PaystackConfig()


class MonitoringConfig(BaseModel):
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 1.0
    sentry_profiles_sample_rate: float = 1.0
    enable_health_checks: bool = True
    enable_metrics: bool = False
    metrics_port: int = 9090


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "./logs/app.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_json_logs: bool = False
    enable_sql_logging: bool = False


class BackgroundTasksConfig(BaseModel):
    enabled: bool = True
    max_workers: int = 4
    queue_max_size: int = 100
    retry_attempts: int = 3
    retry_delay_seconds: int = 5

    
class AppConfig(BaseModel):
    general_config: GeneralConfig = GeneralConfig()
    hosting_config: HostingConfig = HostingConfig()
    database_config: DatabaseConfig = DatabaseConfig()
    redis_config: RedisConfig = RedisConfig()
    security_config: SecurityConfig
    oauth_config: OAuthConfig = OAuthConfig()
    ai_config: AIConfig = AIConfig()
    mail_config: MailConfig
    payments_config: PaymentsConfig = PaymentsConfig()
    monitoring_config: MonitoringConfig = MonitoringConfig()
    logging_config: LoggingConfig = LoggingConfig()
    background_tasks_config: BackgroundTasksConfig = BackgroundTasksConfig()
    
    class Config:
        env_nested_delimiter = "__"  # Allows loading nested config from env vars like REDIS_CONFIG__HOST
        case_sensitive = False
        validate_assignment = True  # Validate on attribute assignment
    
    @property
    def is_production(self) -> bool:
        return not self.general_config.development_mode
    
    @property
    def is_testing(self) -> bool:
        return self.general_config.development_mode and "test" in self.database_config.sql_connection_string.lower()

