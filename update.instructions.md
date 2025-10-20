分析此代码库，生成或更新`.github/copilot-instructions.md`文件，用于指导 AI 编码代理工作。

重点关注能帮助 AI 代理快速融入该代码库的核心知识，包括：

- 需要阅读多个文件才能理解的宏观架构——主要组件、服务边界、数据流以及结构设计背后的“原因”
- 关键的开发工作流程（构建、测试、调试），特别是仅通过文件检查难以发现的命令
- 区别于常见实践的项目特定规范和模式
- 集成点、外部依赖以及跨组件通信模式

通过通配符搜索`**/{.github/copilot-instructions.md,AGENT.md,AGENTS.md,CLAUDE.md,.cursorrules,.windsurfrules,.clinerules,.cursor/rules/**,.windsurf/rules/**,.clinerules/**,README.md}`获取现有 AI 规范（执行一次全局搜索）。

编写指南（详见https://aka.ms/vscode-instructions-docs）：

- 若存在`.github/copilot-instructions.md`文件，通过 `.github/copilot-instructions.metadata.json` 中的`range_start_commit`值，运行脚本`python3 .github/copilot-instructions-update/history-commits.py --output .github/latest-changes.md`获取“自上次更新以来”的提交列表，读取文件`.github/latest-changes.md`分析提交的消息和提交所影响的文件，必要时直接读取代码库中发生变更的代码，智能分析代码库发生的变更。智能合并内容——保留有价值部分的同时更新过时章节需智能合并内容。
- 使用 Markdown 结构编写简洁可操作的指南（约 50-100 行）
- 描述模式时包含代码库中的具体示例
- 避免通用建议（如“编写测试”、“处理错误”）——聚焦于本项目特有方案
- 仅记录可发现的模式，而非理想化实践
- 引用体现重要模式的關鍵文件/目录
- 文档更新后运行 `python3 .github/copilot-instructions-update/update-copilot-instructions.metadata.py` 刷新元数据。

完成`.github/copilot-instructions.md`更新后，请就任何不明确或不完整的部分征求用户反馈以进行迭代优化。
