"""Quick sanity check — confirms snowflake_client.py can read profiles.yml and reach Snowflake."""
import sys
import warnings
from pathlib import Path

# suppress vendored-requests version mismatch and connections.toml permission noise
warnings.filterwarnings("ignore", category=UserWarning, module="snowflake")
warnings.filterwarnings("ignore", message=".*urllib3.*|.*chardet.*|.*charset_normalizer.*")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.snowflake_client import execute_query, close_connection

result = execute_query("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_WAREHOUSE()")
row = result[0]
print("Connected successfully:")
print(f"  User      : {row['CURRENT_USER()']}")
print(f"  Role      : {row['CURRENT_ROLE()']}")
print(f"  Database  : {row['CURRENT_DATABASE()']}")
print(f"  Warehouse : {row['CURRENT_WAREHOUSE()']}")
close_connection()
