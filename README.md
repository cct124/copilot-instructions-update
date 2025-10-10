# copilot-instructions-update

用于在任何 Git 仓库中生成“自上次更新以来”的提交变更摘要，并协助维护 AI 代理的项目专属工作指南（`.github/copilot-instructions.md`）。

核心脚本：

- `history-commits.py`：读取 `.github/copilot-instructions.metadata.json` 中的起始提交，分析从该提交以来的变更，输出 Markdown 摘要（可保存到 `.github/latest-changes.md`）。
- `update-copilot-instructions.metadata.py`：更新 `.github/copilot-instructions.metadata.json`（递增文档版本，刷新最近一次更新的提交信息）。

快速使用：

- 分析最近 50 次提交（自动选择起点）
  - 运行后在控制台查看摘要

- 指定起始提交并保存到文件
  - 将摘要保存为 `.github/latest-changes.md`

元数据文件：`.github/copilot-instructions.metadata.json`

- `doc_revision`：文档修订号（每次更新自增）
- `range_start_commit`：下次分析的起始提交（通常设置为最新提交）
- `last_update`：上次更新的详细信息（提交、作者、时间、分支）

协作建议：

- 将 `.github/copilot-instructions.md` 作为 AI 代理的“入门地图”，描述项目特有模式与工作流。
- 每次更新完该文档后，运行元数据更新脚本，保持提交范围准确。
- 克隆进仓库时不想把它当子模块提交，可以把它从索引移，使用指令`git rm --cached .github/copilot-instructions-update`

许可：MIT License
