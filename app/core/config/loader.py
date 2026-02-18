# v2 - direct import - explicit is better than implicit - python-zen

import os
from pathlib import Path
import yaml
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from .models import (
    AppConfig,
    GeneralConfig,
    HostingConfig,
    CookieConfig,
    ContentDeliveryConfig,
    S3ApiConfig,
    DatabaseConfig,
    RedisConfig,
    SecurityConfig,
    OAuthConfig,
    AIConfig,
    ChromaDBConfig,
    MailConfig,
    PaymentsConfig,
    StripeConfig,
    PaystackConfig,
    MonitoringConfig,
    LoggingConfig,
    BackgroundTasksConfig,
)


class ConfigLoader:
    """Loads application configuration from environment variables and YAML files."""
    
    # def __init__(self):
    #     """Initialize the config loader and load environment variables."""
    #     load_dotenv(override=True)
    #     self.yaml_config = self._load_yaml_config()
    
    # def __init__(self):
    #     """Initialize the config loader and load environment variables."""
    #     # Explicit path to .env file
    #     dotenv_path = '/home/simpdinr/api-studentscores.simplylovely.ng/.env'
    #     load_dotenv(dotenv_path, override=True)
        
    #     self.yaml_config = self._load_yaml_config()
    
    
    # def __init__(self):
    #     """Initialize the config loader and load environment variables."""
    #     # Get the absolute path to the .env file
    #     # Go up from config/loader.py -> config/ -> app/ -> project root
    #     current_file = Path(__file__).resolve()
    #     project_root = current_file.parent.parent.parent  # Go up 3 levels
    #     dotenv_path = project_root / '.env'
        
    #     # Load with explicit path
    #     load_dotenv(dotenv_path, override=True)
        
    #     self.yaml_config = self._load_yaml_config()

    # v2 - debug mode
    def __init__(self):
        """Initialize the config loader and load environment variables."""
        # Get absolute path to .env file
        # Go up from: loader.py -> config/ -> core/ -> app/ -> project_root/
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        dotenv_path = project_root / '.env'
        
        # Debug: print the path (remove after confirming it works)
        print(f"Loading .env from: {dotenv_path}")
        print(f".env exists: {dotenv_path.exists()}")
        
        # Load with explicit path
        load_dotenv(dotenv_path, override=True)
        
        self.yaml_config = self._load_yaml_config()
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load YAML configuration file."""
        yaml_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _get_value(
        self, 
        env_key: str, 
        yaml_path: List[str], 
        default: Any = None, 
        transform=None
    ) -> Any:
        """
        Get value from environment or YAML with fallback.
        
        Args:
            env_key: Environment variable key
            yaml_path: Path to value in YAML config
            default: Default value if not found
            transform: Optional transformation function
            
        Returns:
            The configuration value
        """
        # Environment variable takes precedence
        env_value = os.environ.get(env_key)
        if env_value not in [None, "None", ""]:
            value = env_value
        else:
            # Fall back to YAML config
            yaml_value = self.yaml_config
            for key in yaml_path:
                yaml_value = yaml_value.get(key, {}) if isinstance(yaml_value, dict) else {}
            value = yaml_value if yaml_value != {} else default
        
        # Apply transformation if provided
        if transform and value is not None:
            return transform(value)
        return value
    
    def _to_bool(self, value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'y', 'on']
        return bool(value)
    
    def _to_int(self, value: Any) -> int:
        """Convert value to integer."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    
    def _to_float(self, value: Any) -> float:
        """Convert value to float."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    
    def _to_list(self, value: Any) -> List[str]:
        """Convert comma-separated string to list."""
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return []
    
    def _to_dict_list(self, value: Any) -> List[Dict]:
        """Convert string representation of list of dicts."""
        if isinstance(value, list):
            return value
        # For simple string format, you might need custom parsing
        # This is a placeholder - adjust based on your actual format
        return []
    
    def load_config(self) -> AppConfig:
        """
        Load and return the complete application configuration.
        
        Returns:
            AppConfig: Complete application configuration
            
        Raises:
            ValueError: If required configuration values are missing
        """
        # Security - required field
        auth_jwt_secret_key = self._get_value(
            "APP_AUTH_JWT_SECRET_KEY",
            ["security", "auth_jwt_secret_key"]
        )
        
        if not auth_jwt_secret_key:
            raise ValueError(f"APP_AUTH_JWT_SECRET_KEY is required")
        
        # Build configuration
        return AppConfig(
            general_config=GeneralConfig(
                development_mode=self._get_value(
                    "APP_DEVELOPMENT_MODE", 
                    ["general", "development_mode"], 
                    False, 
                    self._to_bool
                ),
                install_mode=self._get_value(
                    "APP_INSTALL_MODE", 
                    ["general", "install_mode"], 
                    False, 
                    self._to_bool
                ),
                api_prefix=self._get_value(
                    "APP_API_PREFIX",
                    ["general", "api_prefix"],
                    "/api/v1"
                ),
                site_name=self._get_value(
                    "APP_SITE_NAME", 
                    ["general", "site_name"], 
                    "Dunistech Academy"
                ),
                site_description=self._get_value(
                    "APP_SITE_DESCRIPTION", 
                    ["general", "site_description"], 
                    "Learning Management System"
                ),
                contact_email=self._get_value(
                    "APP_CONTACT_EMAIL", 
                    ["general", "contact_email"], 
                    "admin@dunistechacademy.ng"
                ),
                timezone=self._get_value(
                    "APP_TIMEZONE",
                    ["general", "timezone"],
                    "Africa/Lagos"
                )
            ),
            
            hosting_config=HostingConfig(
                domain=self._get_value(
                    "APP_DOMAIN", 
                    ["hosting_config", "domain"], 
                    "localhost"
                ),
                ssl=self._get_value(
                    "APP_SSL", 
                    ["hosting_config", "ssl"], 
                    False, 
                    self._to_bool
                ),
                port=self._get_value(
                    "APP_PORT", 
                    ["hosting_config", "port"], 
                    8000, 
                    self._to_int
                ),
                use_default_org=self._get_value(
                    "APP_USE_DEFAULT_ORG", 
                    ["hosting_config", "use_default_org"], 
                    True, 
                    self._to_bool
                ),
                allowed_origins=self._get_value(
                    "APP_ALLOWED_ORIGINS", 
                    ["hosting_config", "allowed_origins"], 
                    ["http://localhost:3000"], 
                    self._to_list
                ),
                allowed_regexp=self._get_value(
                    "APP_ALLOWED_REGEXP", 
                    ["hosting_config", "allowed_regexp"], 
                    ""
                ),
                self_hosted=self._get_value(
                    "APP_SELF_HOSTED", 
                    ["hosting_config", "self_hosted"], 
                    True, 
                    self._to_bool
                ),
                api_url=self._get_value(
                    "APP_API_URL",
                    ["hosting_config", "api_url"],
                    "http://localhost:8000"
                ),
                frontend_url=self._get_value(
                    "APP_FRONTEND_URL",
                    ["hosting_config", "frontend_url"],
                    "http://localhost:3000"
                ),
                cookie_config=CookieConfig(
                    domain=self._get_value(
                        "APP_COOKIE_DOMAIN", 
                        ["hosting_config", "cookies_config", "domain"], 
                        "localhost"
                    ),
                    secure=self._get_value(
                        "APP_COOKIE_SECURE",
                        ["hosting_config", "cookies_config", "secure"],
                        False,
                        self._to_bool
                    ),
                    httponly=self._get_value(
                        "APP_COOKIE_HTTPONLY",
                        ["hosting_config", "cookies_config", "httponly"],
                        True,
                        self._to_bool
                    ),
                    samesite=self._get_value(
                        "APP_COOKIE_SAMESITE",
                        ["hosting_config", "cookies_config", "samesite"],
                        "lax"
                    ),
                    max_age=self._get_value(
                        "APP_COOKIE_MAX_AGE",
                        ["hosting_config", "cookies_config", "max_age"],
                        60 * 60 * 24 * 7,
                        self._to_int
                    )
                ),
                content_delivery=ContentDeliveryConfig(
                    type=self._get_value(
                        "APP_CONTENT_DELIVERY_TYPE", 
                        ["hosting_config", "content_delivery", "type"], 
                        "filesystem"
                    ),
                    filesystem_base_path=self._get_value(
                        "APP_FILESYSTEM_BASE_PATH",
                        ["hosting_config", "content_delivery", "filesystem_base_path"],
                        "./uploads"
                    ),
                    max_file_size_mb=self._get_value(
                        "APP_MAX_FILE_SIZE_MB",
                        ["hosting_config", "content_delivery", "max_file_size_mb"],
                        100,
                        self._to_int
                    ),
                    allowed_file_types=self._get_value(
                        "APP_ALLOWED_FILE_TYPES",
                        ["hosting_config", "content_delivery", "allowed_file_types"],
                        ["image/jpeg", "image/png", "image/gif", "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                        self._to_list
                    ),
                    s3api=S3ApiConfig(
                        bucket_name=self._get_value(
                            "APP_S3_API_BUCKET_NAME", 
                            ["hosting_config", "content_delivery", "s3api", "bucket_name"]
                        ),
                        endpoint_url=self._get_value(
                            "APP_S3_API_ENDPOINT_URL", 
                            ["hosting_config", "content_delivery", "s3api", "endpoint_url"]
                        ),
                        region=self._get_value(
                            "APP_S3_API_REGION",
                            ["hosting_config", "content_delivery", "s3api", "region"],
                            "us-east-1"
                        ),
                        access_key_id=self._get_value(
                            "APP_S3_API_ACCESS_KEY_ID",
                            ["hosting_config", "content_delivery", "s3api", "access_key_id"]
                        ),
                        secret_access_key=self._get_value(
                            "APP_S3_API_SECRET_ACCESS_KEY",
                            ["hosting_config", "content_delivery", "s3api", "secret_access_key"]
                        ),
                        use_ssl=self._get_value(
                            "APP_S3_API_USE_SSL",
                            ["hosting_config", "content_delivery", "s3api", "use_ssl"],
                            True,
                            self._to_bool
                        ),
                        signature_version=self._get_value(
                            "APP_S3_API_SIGNATURE_VERSION",
                            ["hosting_config", "content_delivery", "s3api", "signature_version"],
                            "s3v4"
                        )
                    )
                )
            ),
            
            database_config=DatabaseConfig(
                sql_connection_string=self._get_value(
                    "APP_SQL_CONNECTION_STRING", 
                    ["database_config", "sql_connection_string"]
                ),
                pool_size=self._get_value(
                    "APP_DB_POOL_SIZE",
                    ["database_config", "pool_size"],
                    20,
                    self._to_int
                ),
                max_overflow=self._get_value(
                    "APP_DB_MAX_OVERFLOW",
                    ["database_config", "max_overflow"],
                    40,
                    self._to_int
                ),
                pool_recycle=self._get_value(
                    "APP_DB_POOL_RECYCLE",
                    ["database_config", "pool_recycle"],
                    3600,
                    self._to_int
                ),
                pool_timeout=self._get_value(
                    "APP_DB_POOL_TIMEOUT",
                    ["database_config", "pool_timeout"],
                    30,
                    self._to_int
                ),
                echo=self._get_value(
                    "APP_DB_ECHO",
                    ["database_config", "echo"],
                    False,
                    self._to_bool
                )
            ),
            
            redis_config=RedisConfig(
                redis_connection_string=self._get_value(
                    "APP_REDIS_CONNECTION_STRING", 
                    ["redis_config", "redis_connection_string"]
                ),
                host=self._get_value(
                    "APP_REDIS_HOST",
                    ["redis_config", "host"],
                    "localhost"
                ),
                port=self._get_value(
                    "APP_REDIS_PORT",
                    ["redis_config", "port"],
                    6379,
                    self._to_int
                ),
                db=self._get_value(
                    "APP_REDIS_DB",
                    ["redis_config", "db"],
                    0,
                    self._to_int
                ),
                password=self._get_value(
                    "APP_REDIS_PASSWORD",
                    ["redis_config", "password"]
                ),
                username=self._get_value(
                    "APP_REDIS_USERNAME",
                    ["redis_config", "username"]
                ),
                ssl=self._get_value(
                    "APP_REDIS_SSL",
                    ["redis_config", "ssl"],
                    False,
                    self._to_bool
                ),
                ssl_cert_reqs=self._get_value(
                    "APP_REDIS_SSL_CERT_REQS",
                    ["redis_config", "ssl_cert_reqs"]
                ),
                connection_pool_size=self._get_value(
                    "APP_REDIS_CONNECTION_POOL_SIZE",
                    ["redis_config", "connection_pool_size"],
                    10,
                    self._to_int
                ),
                socket_timeout=self._get_value(
                    "APP_REDIS_SOCKET_TIMEOUT",
                    ["redis_config", "socket_timeout"],
                    5,
                    self._to_int
                ),
                socket_connect_timeout=self._get_value(
                    "APP_REDIS_SOCKET_CONNECT_TIMEOUT",
                    ["redis_config", "socket_connect_timeout"],
                    5,
                    self._to_int
                ),
                retry_on_timeout=self._get_value(
                    "APP_REDIS_RETRY_ON_TIMEOUT",
                    ["redis_config", "retry_on_timeout"],
                    True,
                    self._to_bool
                ),
                decode_responses=self._get_value(
                    "APP_REDIS_DECODE_RESPONSES",
                    ["redis_config", "decode_responses"],
                    True,
                    self._to_bool
                ),
                default_ttl=self._get_value(
                    "APP_REDIS_DEFAULT_TTL",
                    ["redis_config", "default_ttl"],
                    3600,
                    self._to_int
                ),
                session_ttl=self._get_value(
                    "APP_REDIS_SESSION_TTL",
                    ["redis_config", "session_ttl"],
                    86400,
                    self._to_int
                ),
                rate_limit_ttl=self._get_value(
                    "APP_REDIS_RATE_LIMIT_TTL",
                    ["redis_config", "rate_limit_ttl"],
                    60,
                    self._to_int
                ),
                use_sentinel=self._get_value(
                    "APP_REDIS_USE_SENTINEL",
                    ["redis_config", "use_sentinel"],
                    False,
                    self._to_bool
                ),
                sentinel_nodes=self._get_value(
                    "APP_REDIS_SENTINEL_NODES",
                    ["redis_config", "sentinel_nodes"],
                    [],
                    self._to_dict_list
                ),
                sentinel_service_name=self._get_value(
                    "APP_REDIS_SENTINEL_SERVICE_NAME",
                    ["redis_config", "sentinel_service_name"],
                    "mymaster"
                ),
                sentinel_password=self._get_value(
                    "APP_REDIS_SENTINEL_PASSWORD",
                    ["redis_config", "sentinel_password"]
                )
            ),
            
            security_config=SecurityConfig(
                auth_jwt_secret_key=auth_jwt_secret_key,
                jwt_algorithm=self._get_value(
                    "APP_JWT_ALGORITHM",
                    ["security_config", "jwt_algorithm"],
                    "HS256"
                ),
                access_token_expire_minutes=self._get_value(
                    "APP_ACCESS_TOKEN_EXPIRE_MINUTES",
                    ["security_config", "access_token_expire_minutes"],
                    60 * 24,
                    self._to_int
                ),
                refresh_token_expire_minutes=self._get_value(
                    "APP_REFRESH_TOKEN_EXPIRE_MINUTES",
                    ["security_config", "refresh_token_expire_minutes"],
                    60 * 24 * 7,
                    self._to_int
                ),
                jwt_secret_key=self._get_value(
                    "APP_JWT_FALLBACK_KEY",
                    ["security_config", "jwt_secret_key"],
                    "SUPER_SECRET_KEY_EDET_JAMES"
                ),
                password_reset_token_expire_minutes=self._get_value(
                    "APP_PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
                    ["security_config", "password_reset_token_expire_minutes"],
                    15,
                    self._to_int
                ),
                email_verification_token_expire_minutes=self._get_value(
                    "APP_EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES",
                    ["security_config", "email_verification_token_expire_minutes"],
                    60 * 24,
                    self._to_int
                ),
                bcrypt_rounds=self._get_value(
                    "APP_BCRYPT_ROUNDS",
                    ["security_config", "bcrypt_rounds"],
                    12,
                    self._to_int
                ),
                cors_allowed_origins=self._get_value(
                    "APP_CORS_ALLOWED_ORIGINS",
                    ["security_config", "cors_allowed_origins"],
                    ["http://localhost:3000", "http://localhost:8000"],
                    self._to_list
                )
            ),
            
            oauth_config=OAuthConfig(
                google_client_id=self._get_value(
                    "APP_GOOGLE_CLIENT_ID",
                    ["oauth_config", "google_client_id"]
                ),
                google_client_secret=self._get_value(
                    "APP_GOOGLE_CLIENT_SECRET",
                    ["oauth_config", "google_client_secret"]
                ),
                google_redirect_uri=self._get_value(
                    "APP_GOOGLE_REDIRECT_URI",
                    ["oauth_config", "google_redirect_uri"]
                ),
                facebook_client_id=self._get_value(
                    "APP_FACEBOOK_CLIENT_ID",
                    ["oauth_config", "facebook_client_id"]
                ),
                facebook_client_secret=self._get_value(
                    "APP_FACEBOOK_CLIENT_SECRET",
                    ["oauth_config", "facebook_client_secret"]
                ),
                facebook_redirect_uri=self._get_value(
                    "APP_FACEBOOK_REDIRECT_URI",
                    ["oauth_config", "facebook_redirect_uri"]
                ),
                twitter_client_id=self._get_value(
                    "APP_TWITTER_CLIENT_ID",
                    ["oauth_config", "twitter_client_id"]
                ),
                twitter_client_secret=self._get_value(
                    "APP_TWITTER_CLIENT_SECRET",
                    ["oauth_config", "twitter_client_secret"]
                ),
                twitter_redirect_uri=self._get_value(
                    "APP_TWITTER_REDIRECT_URI",
                    ["oauth_config", "twitter_redirect_uri"]
                )
            ),
            
            ai_config=AIConfig(
                openai_api_key=self._get_value(
                    "APP_OPENAI_API_KEY", 
                    ["ai_config", "openai_api_key"]
                ),
                anthropic_api_key=self._get_value(
                    "APP_ANTHROPIC_API_KEY",
                    ["ai_config", "anthropic_api_key"]
                ),
                google_api_key=self._get_value(
                    "APP_GOOGLE_API_KEY",
                    ["ai_config", "google_api_key"]
                ),
                is_ai_enabled=self._get_value(
                    "APP_IS_AI_ENABLED", 
                    ["ai_config", "is_ai_enabled"], 
                    False, 
                    self._to_bool
                ),
                default_model=self._get_value(
                    "APP_DEFAULT_AI_MODEL",
                    ["ai_config", "default_model"],
                    "gpt-3.5-turbo"
                ),
                embedding_model=self._get_value(
                    "APP_EMBEDDING_MODEL",
                    ["ai_config", "embedding_model"],
                    "text-embedding-ada-002"
                ),
                chromadb_config=ChromaDBConfig(
                    is_separate_database_enabled=self._get_value(
                        "APP_CHROMADB_SEPARATE", 
                        ["ai_config", "chromadb_config", "isSeparateDatabaseEnabled"], 
                        False, 
                        self._to_bool
                    ),
                    db_host=self._get_value(
                        "APP_CHROMADB_HOST", 
                        ["ai_config", "chromadb_config", "db_host"]
                    ),
                    persist_directory=self._get_value(
                        "APP_CHROMADB_PERSIST_DIRECTORY",
                        ["ai_config", "chromadb_config", "persist_directory"],
                        "./chromadb_data"
                    ),
                    collection_name=self._get_value(
                        "APP_CHROMADB_COLLECTION_NAME",
                        ["ai_config", "chromadb_config", "collection_name"],
                        "academy_documents"
                    )
                )
            ),
            
            mail_config=MailConfig(
                system_email_address=self._get_value(
                    "APP_SYSTEM_EMAIL_ADDRESS",
                    ["mail_config", "system_email_address"],
                    "no-reply@dunistech.ng"
                ),
                mail_sender_name=self._get_value(
                    "APP_MAIL_SENDER_NAME",
                    ["mail_config", "mail_sender_name"],
                    "Dunistech Academy"
                ),
                mail_sender_email=self._get_value(
                    "APP_MAIL_SENDER_EMAIL",
                    ["mail_config", "mail_sender_email"],
                    "no-reply@dunistech.ng"
                ),
                provider=self._get_value(
                    "APP_MAIL_PROVIDER",
                    ["mail_config", "provider"],
                    "smtp"
                ),
                smtp_host=self._get_value(
                    "APP_SMTP_HOST",
                    ["mail_config", "smtp_host"],
                    "smtp.gmail.com"
                ),
                smtp_port=self._get_value(
                    "APP_SMTP_PORT",
                    ["mail_config", "smtp_port"],
                    587,
                    self._to_int
                ),
                smtp_username=self._get_value(
                    "APP_SMTP_USERNAME",
                    ["mail_config", "smtp_username"]
                ),
                smtp_password=self._get_value(
                    "APP_SMTP_PASSWORD",
                    ["mail_config", "smtp_password"]
                ),
                smtp_use_tls=self._get_value(
                    "APP_SMTP_USE_TLS",
                    ["mail_config", "smtp_use_tls"],
                    True,
                    self._to_bool
                ),
                smtp_use_ssl=self._get_value(
                    "APP_SMTP_USE_SSL",
                    ["mail_config", "smtp_use_ssl"],
                    False,
                    self._to_bool
                ),
                smtp_timeout=self._get_value(
                    "APP_SMTP_TIMEOUT",
                    ["mail_config", "smtp_timeout"],
                    30,
                    self._to_int
                ),
                resend_api_key=self._get_value(
                    "APP_RESEND_API_KEY", 
                    ["mail_config", "resend_api_key"]
                ),
                sendgrid_api_key=self._get_value(
                    "APP_SENDGRID_API_KEY",
                    ["mail_config", "sendgrid_api_key"]
                ),
                mailgun_api_key=self._get_value(
                    "APP_MAILGUN_API_KEY",
                    ["mail_config", "mailgun_api_key"]
                ),
                mailgun_domain=self._get_value(
                    "APP_MAILGUN_DOMAIN",
                    ["mail_config", "mailgun_domain"]
                ),
                templates_dir=self._get_value(
                    "APP_EMAIL_TEMPLATES_DIR",
                    ["mail_config", "templates_dir"],
                    "./email_templates"
                ),
                emails_per_hour=self._get_value(
                    "APP_EMAILS_PER_HOUR",
                    ["mail_config", "emails_per_hour"],
                    100,
                    self._to_int
                ),
                retry_attempts=self._get_value(
                    "APP_EMAIL_RETRY_ATTEMPTS",
                    ["mail_config", "retry_attempts"],
                    3,
                    self._to_int
                )
            ),
            
            payments_config=PaymentsConfig(
                default_provider=self._get_value(
                    "APP_PAYMENTS_DEFAULT_PROVIDER",
                    ["payments_config", "default_provider"],
                    "none"
                ),
                currency=self._get_value(
                    "APP_PAYMENTS_CURRENCY",
                    ["payments_config", "currency"],
                    "NGN"
                ),
                stripe=StripeConfig(
                    secret_key=self._get_value(
                        "APP_STRIPE_SECRET_KEY", 
                        ["payments_config", "stripe", "secret_key"]
                    ),
                    publishable_key=self._get_value(
                        "APP_STRIPE_PUBLISHABLE_KEY", 
                        ["payments_config", "stripe", "publishable_key"]
                    ),
                    webhook_standard_secret=self._get_value(
                        "APP_STRIPE_WEBHOOK_STANDARD_SECRET", 
                        ["payments_config", "stripe", "webhook_standard_secret"]
                    ),
                    webhook_connect_secret=self._get_value(
                        "APP_STRIPE_WEBHOOK_CONNECT_SECRET", 
                        ["payments_config", "stripe", "webhook_connect_secret"]
                    ),
                    client_id=self._get_value(
                        "APP_STRIPE_CLIENT_ID", 
                        ["payments_config", "stripe", "client_id"]
                    ),
                    api_version=self._get_value(
                        "APP_STRIPE_API_VERSION",
                        ["payments_config", "stripe", "api_version"],
                        "2023-10-16"
                    ),
                    max_network_retries=self._get_value(
                        "APP_STRIPE_MAX_NETWORK_RETRIES",
                        ["payments_config", "stripe", "max_network_retries"],
                        2,
                        self._to_int
                    ),
                    timeout=self._get_value(
                        "APP_STRIPE_TIMEOUT",
                        ["payments_config", "stripe", "timeout"],
                        30,
                        self._to_int
                    )
                ),
                paystack=PaystackConfig(
                    secret_key=self._get_value(
                        "APP_PAYSTACK_SECRET_KEY", 
                        ["payments_config", "paystack", "secret_key"]
                    ),
                    public_key=self._get_value(
                        "APP_PAYSTACK_PUBLIC_KEY", 
                        ["payments_config", "paystack", "public_key"]
                    ),
                    base_url=self._get_value(
                        "APP_PAYSTACK_BASE_URL", 
                        ["payments_config", "paystack", "base_url"], 
                        "https://api.paystack.co"
                    ),
                    callback_url=self._get_value(
                        "APP_PAYSTACK_CALLBACK_URL",
                        ["payments_config", "paystack", "callback_url"]
                    ),
                    timeout=self._get_value(
                        "APP_PAYSTACK_TIMEOUT",
                        ["payments_config", "paystack", "timeout"],
                        30,
                        self._to_int
                    )
                )
            ),
            
            monitoring_config=MonitoringConfig(
                sentry_dsn=self._get_value(
                    "APP_SENTRY_DSN",
                    ["monitoring_config", "sentry_dsn"]
                ),
                sentry_environment=self._get_value(
                    "APP_SENTRY_ENVIRONMENT",
                    ["monitoring_config", "sentry_environment"],
                    "development"
                ),
                sentry_traces_sample_rate=self._get_value(
                    "APP_SENTRY_TRACES_SAMPLE_RATE",
                    ["monitoring_config", "sentry_traces_sample_rate"],
                    1.0,
                    self._to_float
                ),
                sentry_profiles_sample_rate=self._get_value(
                    "APP_SENTRY_PROFILES_SAMPLE_RATE",
                    ["monitoring_config", "sentry_profiles_sample_rate"],
                    1.0,
                    self._to_float
                ),
                enable_health_checks=self._get_value(
                    "APP_ENABLE_HEALTH_CHECKS",
                    ["monitoring_config", "enable_health_checks"],
                    True,
                    self._to_bool
                ),
                enable_metrics=self._get_value(
                    "APP_ENABLE_METRICS",
                    ["monitoring_config", "enable_metrics"],
                    False,
                    self._to_bool
                ),
                metrics_port=self._get_value(
                    "APP_METRICS_PORT",
                    ["monitoring_config", "metrics_port"],
                    9090,
                    self._to_int
                )
            ),
            
            logging_config=LoggingConfig(
                level=self._get_value(
                    "APP_LOGGING_LEVEL",
                    ["logging_config", "level"],
                    "INFO"
                ),
                format=self._get_value(
                    "APP_LOGGING_FORMAT",
                    ["logging_config", "format"],
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
                file_path=self._get_value(
                    "APP_LOGGING_FILE_PATH",
                    ["logging_config", "file_path"],
                    "./logs/app.log"
                ),
                max_file_size_mb=self._get_value(
                    "APP_LOGGING_MAX_FILE_SIZE_MB",
                    ["logging_config", "max_file_size_mb"],
                    100,
                    self._to_int
                ),
                backup_count=self._get_value(
                    "APP_LOGGING_BACKUP_COUNT",
                    ["logging_config", "backup_count"],
                    5,
                    self._to_int
                ),
                enable_json_logs=self._get_value(
                    "APP_LOGGING_ENABLE_JSON_LOGS",
                    ["logging_config", "enable_json_logs"],
                    False,
                    self._to_bool
                ),
                enable_sql_logging=self._get_value(
                    "APP_LOGGING_ENABLE_SQL_LOGGING",
                    ["logging_config", "enable_sql_logging"],
                    False,
                    self._to_bool
                )
            ),
            
            background_tasks_config=BackgroundTasksConfig(
                enabled=self._get_value(
                    "APP_BACKGROUND_TASKS_ENABLED",
                    ["background_tasks_config", "enabled"],
                    True,
                    self._to_bool
                ),
                max_workers=self._get_value(
                    "APP_BACKGROUND_TASKS_MAX_WORKERS",
                    ["background_tasks_config", "max_workers"],
                    4,
                    self._to_int
                ),
                queue_max_size=self._get_value(
                    "APP_BACKGROUND_TASKS_QUEUE_MAX_SIZE",
                    ["background_tasks_config", "queue_max_size"],
                    100,
                    self._to_int
                ),
                retry_attempts=self._get_value(
                    "APP_BACKGROUND_TASKS_RETRY_ATTEMPTS",
                    ["background_tasks_config", "retry_attempts"],
                    3,
                    self._to_int
                ),
                retry_delay_seconds=self._get_value(
                    "APP_BACKGROUND_TASKS_RETRY_DELAY_SECONDS",
                    ["background_tasks_config", "retry_delay_seconds"],
                    5,
                    self._to_int
                )
            )
        )
    
