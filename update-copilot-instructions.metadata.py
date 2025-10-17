#!/usr/bin/env python3
"""
Update Copilot Instructions Metadata Script

这个脚本用于自动更新copilot-instructions.metadata.json文件，
在每次文档更新后运行，自动刷新元数据信息。

主要功能：
1. 获取当前最新的提交信息
2. 更新metadata.json中的元数据
3. 递增文档版本号
"""

import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class MetadataUpdater:
    def __init__(self, repo_path: str = "."):
        """初始化元数据更新器

        Args:
            repo_path: Git仓库路径，默认为当前目录
        """
        self.repo_path = Path(repo_path)
        self.metadata_file = (
            self.repo_path / ".github" / "copilot-instructions.metadata.json"
        )

    def run_git_command(self, command: list) -> str:
        """运行git命令并返回输出"""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git命令执行失败: {' '.join(command)}")
            print(f"错误输出: {e.stderr}")
            return ""

    def get_current_commit_info(self) -> Dict[str, str]:
        """获取当前HEAD提交的详细信息"""
        commit_hash = self.run_git_command(["rev-parse", "HEAD"])
        author_name = self.run_git_command(["log", "-1", "--pretty=format:%an"])
        author_email = self.run_git_command(["log", "-1", "--pretty=format:%ae"])
        commit_date = self.run_git_command(["log", "-1", "--pretty=format:%ai"])
        branch_name = self.run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])

        return {
            "commit": commit_hash,
            "author_name": author_name,
            "author_email": author_email,
            "datetime": commit_date,
            "branch": branch_name,
        }

    def load_existing_metadata(self) -> Dict[str, Any]:
        """加载现有的元数据文件"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
            except json.JSONDecodeError as e:
                print(f"警告：解析现有元数据文件失败 - {e}")
                return {}
            except Exception as e:
                print(f"警告：读取现有元数据文件失败 - {e}")
                return {}
        else:
            print("元数据文件不存在，将创建新文件")
            return {}

    def create_updated_metadata(
        self, existing_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建更新后的元数据，保留未识别字段，并写入 last_update 结构"""
        current_commit_info = self.get_current_commit_info()

        # 递增文档版本号
        current_revision = int(existing_metadata.get("doc_revision", 0) or 0)
        new_revision = current_revision + 1

        # 基于现有元数据进行更新（保留额外键）
        updated_metadata: Dict[str, Any] = dict(existing_metadata)
        updated_metadata["doc_revision"] = new_revision
        updated_metadata["range_start_commit"] = current_commit_info["commit"]
        updated_metadata["last_update"] = {
            "commit": current_commit_info["commit"],
            "author": {
                "name": current_commit_info["author_name"],
                "email": current_commit_info["author_email"],
            },
            "datetime": current_commit_info["datetime"],
            "branch": current_commit_info["branch"],
        }

        return updated_metadata

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """保存元数据到文件"""
        # 确保.github目录存在
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(
                    metadata,
                    f,
                    indent=2,
                    ensure_ascii=False
                )
            print(f"元数据已成功更新到: {self.metadata_file}")
        except Exception as e:
            print(f"保存元数据文件失败: {e}")
            sys.exit(1)

    def update_metadata(self, commit_message: Optional[str] = None) -> None:
        """更新元数据的主函数

        Args:
            commit_message: 可选的提交消息，用于创建新的提交
        """
        print("正在更新copilot-instructions元数据...")

        # 加载现有元数据
        existing_metadata = self.load_existing_metadata()

        # 创建更新后的元数据
        updated_metadata = self.create_updated_metadata(existing_metadata)

        # 保存元数据
        self.save_metadata(updated_metadata)

        # 显示更新信息
        self.display_update_info(existing_metadata, updated_metadata)

        # 如果提供了提交消息，则创建新的提交
        if commit_message:
            self.create_commit(commit_message)

    def display_update_info(
        self, old_metadata: Dict[str, Any], new_metadata: Dict[str, Any]
    ) -> None:
        """显示更新信息"""
        print("\n" + "=" * 50)
        print("元数据更新信息")
        print("=" * 50)

    old_revision = old_metadata.get("doc_revision", 0)
        new_revision = new_metadata["doc_revision"]
    last_update = new_metadata.get("last_update", {})

    print(f"文档版本: {old_revision} → {new_revision}")
    print(f"起始提交: {new_metadata['range_start_commit'][:8]}...")
    print(f"更新作者: {last_update.get('author', {}).get('name', 'N/A')}")
    print(f"更新时间: {last_update.get('datetime', 'N/A')}")
    print(f"当前分支: {last_update.get('branch', 'N/A')}")

    def create_commit(self, message: str) -> None:
        """创建一个新的提交包含元数据更新

        Args:
            message: 提交消息
        """
        try:
            # 添加元数据文件到暂存区
            self.run_git_command(["add", str(self.metadata_file)])

            # 创建提交
            self.run_git_command(["commit", "-m", message])

            print(f"\n已创建提交: {message}")
        except Exception as e:
            print(f"创建提交失败: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="更新copilot-instructions元数据文件")
    parser.add_argument("--commit", "-c", type=str, help="创建提交并使用指定的提交消息")
    parser.add_argument(
        "--dry-run", action="store_true", help="只显示将要进行的更改，不实际执行"
    )

    args = parser.parse_args()

    # 检查是否在Git仓库中
    if not os.path.exists(".git"):
        print("错误：当前目录不是Git仓库")
        sys.exit(1)

    updater = MetadataUpdater()

    try:
        if args.dry_run:
            print("执行干运行模式...")
            # 在干运行模式下，只显示当前信息，不进行实际更新
            existing_metadata = updater.load_existing_metadata()
            current_commit_info = updater.get_current_commit_info()

            print("\n当前状态:")
            print(f"当前提交: {current_commit_info['commit'][:8]}...")
            print(f"当前文档版本: {existing_metadata.get('doc_revision', 0)}")
            print(
                f"上次更新提交: {existing_metadata.get('range_start_commit', 'N/A')[:8] if existing_metadata.get('range_start_commit') else 'N/A'}..."
            )

            print("\n将要执行的更新:")
            print(f"新文档版本: {existing_metadata.get('doc_revision', 0) + 1}")
            print(f"新起始提交: {current_commit_info['commit'][:8]}...")
        else:
            updater.update_metadata(args.commit)

    except Exception as e:
        print(f"更新过程中出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
