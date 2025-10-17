#!/usr/bin/env python3
"""
Git History Analysis Script for Copilot Instructions

通用的Git提交历史分析脚本，适用于任何Git仓库。
这个脚本用于分析自上次更新以来的git提交，生成智能化的变更摘要。

主要功能：
1. 从metadata.json读取range_start_commit（可选）
2. 获取从指定提交以来的所有提交记录
3. 分析提交的消息和变更文件
4. 智能分析代码变更并生成摘要
5. 在控制台输出分析结果
"""

import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class GitCommitAnalyzer:
    def __init__(self, repo_path: str = "."):
        """初始化Git提交分析器

        Args:
            repo_path: Git仓库路径，默认为当前目录
        """
        self.repo_path = Path(repo_path)
        self.metadata_file = self.repo_path / ".github" / "copilot-instructions.metadata.json"
        self.copilot_instructions_file = self.repo_path / ".github" / "copilot-instructions.md"

    def load_metadata(self) -> Optional[Dict[str, Any]]:
        """加载copilot-instructions的元数据（如果可用）"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"提示：找不到元数据文件 {self.metadata_file}，将使用默认设置")
            return None
        except json.JSONDecodeError as e:
            print(f"警告：解析JSON文件失败 - {e}，将使用默认设置")
            return None
        except Exception as e:
            print(f"警告：读取元数据文件失败 - {e}，将使用默认设置")
            return None

    def run_git_command(self, command: List[str]) -> str:
        """运行git命令并返回输出"""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',  # 忽略编码错误
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git命令执行失败: {' '.join(command)}")
            print(f"错误输出: {e.stderr}")
            return ""
        except Exception as e:
            print(f"运行Git命令时出现异常: {e}")
            return ""

    def get_commits_since(self, start_commit: str) -> List[Dict[str, Any]]:
        """获取从指定提交以来的所有提交记录（健壮解析）

        使用字段分隔符解析，避免JSON格式在换行/转义上的脆弱性。
        字段分隔符: 0x1F，记录分隔符: 0x1E。
        """
        format_str = "%H%x1f%an%x1f%ae%x1f%ai%x1f%s%x1f%b%x1e"

        commits_output = self.run_git_command([
            "log",
            f"{start_commit}..HEAD",
            f"--pretty=format:{format_str}",
            "--no-merges",
            "--encoding=UTF-8",
        ])

        if not commits_output:
            return []

        records = commits_output.strip("\n\x1e").split("\x1e")
        commits: List[Dict[str, Any]] = []
        for rec in records:
            if not rec:
                continue
            parts = rec.split("\x1f")
            if len(parts) < 5:
                continue
            hash_, author, email, date, subject = parts[:5]
            body = parts[5] if len(parts) > 5 else ""
            commits.append({
                "hash": hash_,
                "author": author,
                "email": email,
                "date": date,
                "message": subject,
                "body": body,
            })

        return commits

    def get_commit_files(self, commit_hash: str) -> List[Dict[str, str]]:
        """获取指定提交涉及的文件变更

        Args:
            commit_hash: 提交hash

        Returns:
            文件变更列表，包含状态（A/M/D）和文件路径
        """
        files_output = self.run_git_command([
            "show",
            "--name-status",
            "--format=",
            commit_hash
        ])

        files = []
        for line in files_output.split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    status = parts[0]
                    # R 或 C 重命名/复制会包含旧/新路径
                    if status.startswith(('R', 'C')) and len(parts) == 3:
                        old_path, new_path = parts[1], parts[2]
                        files.append({
                            'status': status,
                            'path': new_path,
                            'old_path': old_path,
                            'action': self._get_action_description(status)
                        })
                    else:
                        filepath = parts[1]
                        files.append({
                            'status': status,
                            'path': filepath,
                            'action': self._get_action_description(status)
                        })

        return files

    def _get_action_description(self, status: str) -> str:
        """将Git状态转换为可读的操作描述"""
        status_map = {
            'A': '新增',
            'M': '修改',
            'D': '删除',
            'R': '重命名',
            'C': '复制'
        }
        return status_map.get(status[0], '变更')

    def get_file_diff(self, commit_hash: str, filepath: str) -> str:
        """获取指定提交中某个文件的diff

        使用 `git show <commit> -- <path>` 查看该提交相对父提交的差异。
        若需要文件内容可改用 `git show <commit>:<path>`。
        """
        diff_output = self.run_git_command([
            "show",
            "--no-color",
            commit_hash,
            "--",
            filepath
        ])
        return diff_output

    def analyze_commit_impact(self, commit: Dict[str, Any], files: List[Dict[str, str]]) -> Dict[str, Any]:
        """分析单个提交的影响

        Args:
            commit: 提交信息
            files: 该提交涉及的文件列表

        Returns:
            提交影响分析结果
        """
        analysis = {
            'commit': commit,
            'files': files,
            'categories': [],
            'impact_summary': '',
            'key_changes': []
        }

        # 分析文件类型和影响范围
        categories = set()
        key_changes = []

        for file_info in files:
            filepath = file_info['path']
            status = file_info['status']
            action = file_info['action']

            # 通用文件类型分类（不依赖特定项目结构）
            if filepath.endswith(('.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.h')):
                categories.add('源代码')
            elif filepath.endswith(('.md', '.txt', '.rst', '.adoc')):
                categories.add('文档')
            elif filepath.endswith(('.json', '.yaml', '.yml', '.xml', '.ini', '.toml')):
                categories.add('配置文件')
            elif filepath.endswith(('.html', '.css', '.scss', '.less')):
                categories.add('前端资源')
            elif filepath.endswith(('.sql', '.db')):
                categories.add('数据库')
            elif filepath.endswith(('.sh', '.bat', '.ps1')):
                categories.add('脚本文件')
            elif filepath.endswith(('.proto', '.thrift')):
                categories.add('协议定义')
            elif filepath.startswith('.github/'):
                categories.add('CI/CD配置')
                if filepath == '.github/copilot-instructions.md':
                    categories.add('AI 指南')
            elif filepath.startswith('test/') or filepath.startswith('tests/') or 'test' in filepath.lower():
                categories.add('测试文件')
            elif filepath in ['README.md', 'LICENSE', 'CHANGELOG.md', 'CONTRIBUTING.md']:
                categories.add('项目文档')
            elif '.' not in os.path.basename(filepath):
                categories.add('可执行文件')
            else:
                categories.add('其他文件')

            # 生成关键变更描述
            if status in ['A', 'M', 'D']:
                key_changes.append(f"{action} {filepath}")
            elif status.startswith(('R', 'C')):
                old_path = file_info.get('old_path')
                if old_path and old_path != filepath:
                    key_changes.append(f"{action} {old_path} → {filepath}")
                else:
                    key_changes.append(f"{action} {filepath}")

        analysis['categories'] = list(categories)
        analysis['key_changes'] = key_changes

        # 生成影响摘要
        impact_parts = []
        if categories:
            impact_parts.append(f"涉及 {', '.join(categories)}")
        if len(files) > 0:
            impact_parts.append(f"共{len(files)}个文件")

        analysis['impact_summary'] = '; '.join(impact_parts)

        return analysis

    def categorize_changes(self, analyses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将提交分析结果按类别分组

        Args:
            analyses: 提交分析结果列表

        Returns:
            按类别分组的变更
        """
        categorized = {}

        for analysis in analyses:
            for category in analysis['categories']:
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(analysis)

        return categorized

    def get_all_commits(self, max_commits: int = 50) -> List[Dict[str, Any]]:
        """获取所有提交记录（限制数量，健壮解析）"""
        format_str = "%H%x1f%an%x1f%ae%x1f%ai%x1f%s%x1f%b%x1e"

        commits_output = self.run_git_command([
            "log",
            f"-{max_commits}",
            f"--pretty=format:{format_str}",
            "--no-merges",
            "--encoding=UTF-8",
        ])

        if not commits_output:
            return []

        records = commits_output.strip("\n\x1e").split("\x1e")
        commits: List[Dict[str, Any]] = []
        for rec in records:
            if not rec:
                continue
            parts = rec.split("\x1f")
            if len(parts) < 5:
                continue
            hash_, author, email, date, subject = parts[:5]
            body = parts[5] if len(parts) > 5 else ""
            commits.append({
                "hash": hash_,
                "author": author,
                "email": email,
                "date": date,
                "message": subject,
                "body": body,
            })

        return commits

    def generate_change_summary(self, analyses: List[Dict[str, Any]], start_commit: Optional[str] = None) -> str:
        """生成智能化的变更摘要

        Args:
            analyses: 提交分析结果列表
            start_commit: 起始提交hash（可选）

        Returns:
            变更摘要文本
        """
        if not analyses:
            return "没有找到提交记录。"

        summary_lines = [
            f"# Git提交历史分析报告",
            f"",
            f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**提交数量**: {len(analyses)}",
        ]

        if start_commit:
            summary_lines.append(f"**起始提交**: {start_commit}")

        summary_lines.append("")

        # 按类别分组
        categorized = self.categorize_changes(analyses)

        if categorized:
            summary_lines.append("## 变更分类统计")
            summary_lines.append("")

            for category, category_analyses in categorized.items():
                summary_lines.append(f"### {category} ({len(category_analyses)}个提交)")
                summary_lines.append("")

                for analysis in category_analyses[:3]:  # 只显示前3个，避免输出过长
                    commit = analysis['commit']
                    summary_lines.append(f"- **{commit['message']}** ({commit['hash'][:8]})")
                    summary_lines.append(f"  - 作者: {commit['author']}")
                    summary_lines.append(f"  - 时间: {commit['date']}")
                    summary_lines.append(f"  - 影响: {analysis['impact_summary']}")
                    summary_lines.append("")

                if len(category_analyses) > 3:
                    summary_lines.append(f"  ... 还有 {len(category_analyses) - 3} 个提交")
                    summary_lines.append("")

        # 添加详细的提交列表
        summary_lines.extend([
            "## 详细提交记录",
            ""
        ])

        for i, analysis in enumerate(analyses, 1):
            commit = analysis['commit']
            summary_lines.extend([
                f"### {i}. {commit['message']}",
                f"",
                f"- **提交hash**: `{commit['hash']}`",
                f"- **作者**: {commit['author']} <{commit['email']}>",
                f"- **时间**: {commit['date']}",
                f"- **影响范围**: {analysis['impact_summary']}",
                f""
            ])

            if commit['body'].strip():
                summary_lines.extend([
                    "**详细描述**:",
                    "",
                    commit['body'].strip(),
                    ""
                ])

            if analysis['files']:
                summary_lines.append("**变更文件**:")
                summary_lines.append("")
                for file_info in analysis['files'][:10]:  # 限制显示文件数量
                    summary_lines.append(f"- {file_info['action']}: `{file_info['path']}`")
                
                if len(analysis['files']) > 10:
                    summary_lines.append(f"- ... 还有 {len(analysis['files']) - 10} 个文件")
                
                summary_lines.append("")

        return '\n'.join(summary_lines)

    def analyze_repository_changes(self, start_commit: Optional[str] = None, max_commits: int = 50) -> str:
        """分析仓库变更的主入口函数

        Args:
            start_commit: 起始提交hash，如果为None则尝试从metadata读取
            max_commits: 最大分析提交数量，防止输出过长
        """
        print("正在分析Git提交历史...")

        # 如果没有指定起始提交，尝试从元数据加载
        if start_commit is None:
            metadata = self.load_metadata()
            if metadata:
                start_commit = metadata.get('range_start_commit')

        # 如果仍然没有起始提交，使用最近的一些提交
        if not start_commit:
            print("未找到起始提交，将分析最近的提交...")
            # 获取当前分支的最近提交作为参考点
            recent_commits = self.run_git_command(["log", "--oneline", "-10"])
            if recent_commits:
                lines = recent_commits.split('\n')
                if len(lines) > 5:
                    # 使用倒数第5个提交作为起始点
                    start_commit = lines[4].split()[0]
                    print(f"使用最近第5个提交作为起始点: {start_commit}")
                else:
                    print("提交历史较少，将分析所有提交")
                    start_commit = None

        if start_commit:
            print(f"分析从提交 {start_commit} 以来的变更...")
            # 获取提交列表
            commits = self.get_commits_since(start_commit)
        else:
            print("分析所有提交历史...")
            # 获取所有提交（限制数量）
            commits = self.get_all_commits(max_commits)

        if not commits:
            print("没有找到提交记录。")
            return "没有找到提交记录。"

        print(f"找到 {len(commits)} 个提交，正在分析...")

        # 分析每个提交
        analyses = []
        for commit in commits:
            files = self.get_commit_files(commit['hash'])
            analysis = self.analyze_commit_impact(commit, files)
            analyses.append(analysis)

        # 生成摘要
        summary = self.generate_change_summary(analyses, start_commit)

        print("分析完成！")
        return summary

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="分析Git提交历史，生成变更摘要"
    )
    parser.add_argument(
        "--start-commit",
        "-s",
        type=str,
        help="起始提交hash，如果不指定则尝试从metadata.json读取或使用最近的提交"
    )
    parser.add_argument(
        "--max-commits",
        "-m",
        type=int,
        default=50,
        help="最大分析提交数量（默认50）"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="输出文件路径，如果不指定则只在控制台显示"
    )

    args = parser.parse_args()

    # 检查是否在Git仓库中（相对指定 repo_path）
    if not (Path('.') / '.git').exists():
        print("错误：当前目录不是Git仓库")
        sys.exit(1)

    analyzer = GitCommitAnalyzer()

    try:
        summary = analyzer.analyze_repository_changes(
            start_commit=args.start_commit,
            max_commits=args.max_commits
        )

        print("\n" + "="*50)
        print("Git提交历史分析结果:")
        print("="*50)
        print(summary)

        # 如果指定了输出文件，则保存
        if args.output:
            output_file = Path(args.output)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"\n分析结果已保存到: {output_file}")

    except Exception as e:
        print(f"分析过程中出现错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
