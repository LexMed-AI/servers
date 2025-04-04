import argparse
import asyncio
import logging
from pathlib import Path

from .server import main

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SQLite MCP Server")
    parser.add_argument("--db-path", type=str, required=True, help="Path to SQLite database")
    return parser.parse_args()

def run():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    asyncio.run(main(args.db_path))

if __name__ == "__main__":
    run()

# Optionally expose other important items at package level
__all__ = ["main"]
