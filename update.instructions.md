目标：分析当前代码库，生成或更新 `.github/copilot-instructions.md`，用于指导 AI 编码代理的高效协作。

优先梳理能帮助 AI 快速“上手”的项目信息：

- 宏观架构：主要模块/服务边界/数据流与设计动机（跨文件总结）
- 开发工作流：构建/测试/调试的关键命令和约定（仅看文件难以发现的）
- 项目特定规范与模式：命名、目录、代码组织、可复用片段
- 集成点与外部依赖：API、消息总线、CI、环境变量、密钥管理

现有 AI 规范的发现（执行一次全局搜索）：

- 搜索路径：`**/{.github/copilot-instructions.md,AGENT.md,AGENTS.md,CLAUDE.md,.cursorrules,.windsurfrules,.clinerules,.cursor/rules/**,.windsurf/rules/**,.clinerules/**,README.md}`

- 若存在`.github/copilot-instructions.md`文件，通过 `.github/copilot-instructions.metadata.json` 中的`range_start_commit`值，运行脚本`python3 .github/copilot-instructions-update/history-commits.py --output .github/latest-changes.md`获取“自上次更新以来”的提交列表，读取文件`.github/latest-changes.md`分析提交的消息和提交所影响的文件，必要时直接读取代码库中发生变更的代码，智能分析代码库发生的变更。智能合并内容——保留有价值部分的同时更新过时章节需智能合并内容。
- 使用 Markdown 结构编写简洁可操作的指南（约 20-50 行）
- 描述模式时包含代码库中的具体示例
- 避免通用建议（如“编写测试”、“处理错误”）——聚焦于本项目特有方案
- 仅记录可发现的模式，而非理想化实践
- 引用体现重要模式的關鍵文件/目录
- 文档更新后运行 `python3 .github/copilot-instructions-update/update-copilot-instructions.metadata.py` 刷新元数据。

1) 若存在 `.github/copilot-instructions.md`：基于差量变更进行更新
	- 从 `.github/copilot-instructions.metadata.json` 读取 `range_start_commit`
	- 生成“自上次更新以来”的提交清单与摘要：
	  - Windows（bash/Powershell）：`python .github/copilot-instructions-update/history-commits.py --output .github/latest-changes.md`
	  - macOS/Linux：`python3 .github/copilot-instructions-update/history-commits.py --output .github/latest-changes.md`
	- 阅读 `.github/latest-changes.md`，必要时定位具体变更文件，智能合并指南内容：
	  - 保留有效知识，替换过时内容；避免重复段落；引用关键文件/目录

2) 若不存在 `.github/copilot-instructions.md`：创建一个 20-50 行的初版
	- 使用 Markdown 分节，包含：结构总览、运行/调试、约定与示例、风险与注意
	- 示例引用仓库内真实文件与路径

3) 完成更新后刷新元数据（保持下次差量的起点）：
	- Windows：`python .github/copilot-instructions-update/update-copilot-instructions.metadata.py`
	- macOS/Linux：`python3 .github/copilot-instructions-update/update-copilot-instructions.metadata.py`

写作要点：

- 一律记录“实际存在的模式”，不要空泛建议（如“要写测试”）
- 以任务为导向的短句，必要时附 1-2 个代码/命令示例
- 优先覆盖：开发环境、常见陷阱、影响面大的约定、跨模块调用协议

完成 `.github/copilot-instructions.md` 更新后，请就不明确/不完整之处向用户提问以持续迭代。
