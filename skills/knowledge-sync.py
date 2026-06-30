#!/usr/bin/env python3
"""
鲤鱼 Skill: Knowledge Sync — 知识库同步。

同步 memory/ 目录到 SQLite 知识库，确保检索系统数据最新。

Usage:
  knowledge-sync.py sync          同步变更
  knowledge-sync.py status        检查同步状态
  knowledge-sync.py rebuild       重建索引
"""

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

鲤鱼_HOME = Path.home() / ".claude/liyu"
MEMORY_DIR = Path.home() / ".claude/projects/-Users-holyty/memory"
DB_PATH = 鲤鱼_HOME / "knowledge-base.db"
SYNC_STATE_FILE = 鲤鱼_HOME / "knowledge-sync-state.json"


def get_memory_files() -> dict:
    """获取 memory/ 目录的所有文件及修改时间"""
    files = {}

    if not MEMORY_DIR.exists():
        return files

    for md_file in MEMORY_DIR.rglob("*.md"):
        if md_file.name == "MEMORY.md":
            continue

        rel_path = str(md_file.relative_to(MEMORY_DIR))
        mtime = md_file.stat().st_mtime
        files[rel_path] = mtime

    return files


def load_sync_state() -> dict:
    """加载同步状态"""
    if not SYNC_STATE_FILE.exists():
        return {"last_sync": None, "files": {}}

    try:
        return json.loads(SYNC_STATE_FILE.read_text())
    except Exception:
        return {"last_sync": None, "files": {}}


def save_sync_state(state: dict):
    """保存同步状态"""
    SYNC_STATE_FILE.write_text(json.dumps(state, indent=2))


def check_sync_status():
    """检查同步状态"""
    current_files = get_memory_files()
    sync_state = load_sync_state()
    last_sync = sync_state.get("last_sync")
    synced_files = sync_state.get("files", {})

    print("Knowledge Sync Status")
    print("=" * 60)

    if last_sync:
        print(f"Last sync: {last_sync}")
    else:
        print("Last sync: Never")

    print(f"Memory files: {len(current_files)}")
    print(f"Synced files: {len(synced_files)}")
    print()

    # 检查新增或修改的文件
    new_files = []
    modified_files = []

    for rel_path, mtime in current_files.items():
        if rel_path not in synced_files:
            new_files.append(rel_path)
        elif mtime > synced_files[rel_path]:
            modified_files.append(rel_path)

    # 检查删除的文件
    deleted_files = [f for f in synced_files if f not in current_files]

    if new_files:
        print(f"New files ({len(new_files)}):")
        for f in new_files:
            print(f"  + {f}")

    if modified_files:
        print(f"Modified files ({len(modified_files)}):")
        for f in modified_files:
            print(f"  ~ {f}")

    if deleted_files:
        print(f"Deleted files ({len(deleted_files)}):")
        for f in deleted_files:
            print(f"  - {f}")

    if not new_files and not modified_files and not deleted_files:
        print("✓ All files are in sync")

    return len(new_files) + len(modified_files) + len(deleted_files)


def sync():
    """同步变更"""
    # 检查是否需要同步
    changes = check_sync_status()

    if changes == 0:
        print("\nNo changes to sync.")
        return

    print(f"\nSyncing {changes} changes...")

    # 调用 knowledge-base.py import
    import subprocess
    result = subprocess.run(
        ["python3", str(鲤鱼_HOME / "knowledge-base.py"), "import"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(result.stdout)

        # 更新同步状态
        current_files = get_memory_files()
        sync_state = {
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "files": current_files,
        }
        save_sync_state(sync_state)

        print("Sync complete! ✓")
    else:
        print(f"Sync failed: {result.stderr}")


def rebuild():
    """重建索引"""
    print("Rebuilding knowledge base...")

    # 删除旧数据库
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed old database")

    # 删除同步状态
    if SYNC_STATE_FILE.exists():
        SYNC_STATE_FILE.unlink()
        print("Removed sync state")

    # 重新同步
    sync()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "sync":
        sync()

    elif cmd == "status":
        check_sync_status()

    elif cmd == "rebuild":
        rebuild()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
