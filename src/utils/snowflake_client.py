import os
import re
import yaml
import snowflake.connector
from pathlib import Path
from snowflake.connector import SnowflakeConnection
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PrivateFormat, NoEncryption
from src.utils.logger import get_logger

logger = get_logger(__name__)

_connection: SnowflakeConnection | None = None
_DBT_PROFILE = "snowflake_ai_evaluation"


def _load_dbt_credentials() -> dict:
    """Read connection details from ~/.dbt/profiles.yml, resolving env_var() if present."""
    profiles_path = Path.home() / ".dbt" / "profiles.yml"
    with open(profiles_path) as f:
        profiles = yaml.safe_load(f)

    profile = profiles[_DBT_PROFILE]
    target = profile["target"]
    creds = profile["outputs"][target]

    _env_var_re = re.compile(r"\{\{\s*env_var\('([^']+)'(?:,\s*'([^']*)')?\)\s*\}\}")

    def resolve(value):
        if not isinstance(value, str):
            return value
        m = _env_var_re.match(value.strip())
        if m:
            var_name, default = m.group(1), m.group(2)
            return os.environ.get(var_name, default)
        return value

    return {k: resolve(v) for k, v in creds.items()}


def get_connection() -> SnowflakeConnection:
    global _connection
    if _connection is None or _connection.is_closed():
        logger.info("Opening Snowflake connection.")
        c = _load_dbt_credentials()
        auth: dict = {}
        if "private_key_path" in c:
            with open(c["private_key_path"], "rb") as f:
                private_key = load_pem_private_key(f.read(), password=None)
            auth["private_key"] = private_key.private_bytes(
                encoding=Encoding.DER,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption(),
            )
        else:
            auth["password"] = c["password"]
        _connection = snowflake.connector.connect(
            account=c["account"],
            user=c["user"],
            **auth,
            role=c.get("role", "SYSADMIN"),
            database=c.get("database", "ANALYTICS_DB"),
            warehouse=c.get("warehouse", "TRANSFORM_WH"),
            session_parameters={"QUERY_TAG": "snowflake_ai_evaluation"},
        )
    return _connection


def execute_query(sql: str, params: tuple = ()) -> list[dict]:
    conn = get_connection()
    with conn.cursor(snowflake.connector.DictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def close_connection() -> None:
    global _connection
    if _connection and not _connection.is_closed():
        _connection.close()
        logger.info("Snowflake connection closed.")
    _connection = None
