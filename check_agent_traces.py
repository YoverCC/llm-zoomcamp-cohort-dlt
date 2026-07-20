from pathlib import Path
import sys

import duckdb


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    db_path = repo_root / ".dlt" / "data" / "dev" / "logfire_pipeline.duckdb"
    print(f"Using DuckDB file: {db_path}")

    if not db_path.exists():
        print("ERROR: DuckDB file not found.")
        return 1

    conn = duckdb.connect(str(db_path))
    try:
        # Show all tables in the logfire_data schema
        tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'logfire_data';").fetchall()
        print(f"Tables in logfire_data schema: {len(tables)}")
        for row in tables:
            table_name = row[0]
            count = conn.execute(f"SELECT COUNT(*) FROM logfire_data.{table_name}").fetchone()[0]
            print(f"  {table_name:<50} ({count} rows)")
        return 0
    except Exception as exc:
        print("ERROR: failed to execute query:", exc)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
