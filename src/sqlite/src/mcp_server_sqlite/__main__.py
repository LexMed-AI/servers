import asyncio
import argparse
from .server import main

def parse_args():
    parser = argparse.ArgumentParser(description='MCP SQLite Server')
    parser.add_argument('--db-path', required=True, help='Path to SQLite database file')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    asyncio.run(main(args.db_path)) 