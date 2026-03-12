# Knowledge Graph — MCP Server + Agent Skills

从书籍中提取因果规律，构建个人知识图谱，用规律分析真实情境。

本项目包含两个部分：
- **MCP Server** — 提供工具能力（搜索、入库、分析），可被任何支持 MCP 的 agent 调用
- **Agent Skills** — 提供流程知识（怎么读书提取、怎么做情境分析），遵循 [AgentSkills](https://agentskills.io) 开放标准

## 安装

### MCP Server

```bash
pip install knowledge-graph-mcp
```

或从源码：

```bash
git clone https://github.com/stevenlitianyi7/knowledge-graph-plugin.git
cd knowledge-graph-plugin
pip install -e .
```

### Agent Skills

将 `skills/` 目录下的技能文件夹复制到你的 agent 的 skills 目录：

```bash
# Claude Code
cp -r skills/analyze ~/.claude/skills/
cp -r skills/read-book ~/.claude/skills/

# 其他支持 AgentSkills 规范的 agent（Cursor, VS Code Copilot, Gemini CLI 等）
# 参考各自文档配置 skills 路径
```

或在 ClawHub 搜索安装（发布后）。

## 配置 MCP Server

### Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）：

```json
{
  "mcpServers": {
    "knowledge-graph": {
      "command": "knowledge-graph-mcp"
    }
  }
}
```

### Claude Code

```bash
claude mcp add knowledge-graph -- knowledge-graph-mcp
```

### 其他 MCP 客户端

任何支持 MCP 协议的 agent 都可以通过 stdio 传输连接：

```bash
knowledge-graph-mcp
```

## MCP 工具

| 工具 | 作用 |
|------|------|
| `analyze` | 输入情境描述，返回相关规律、因果链和关系网络 |
| `ingest` | 输入提取好的 JSON，入库（自动语义去重） |
| `search` | 关键词搜索节点 |
| `stats` | 返回图谱统计 |
| `gaps` | 返回 ASSUMES 缺口和因果链不完整的现象 |
| `pdf_info` | 获取 PDF 页数和分块信息 |
| `get_node` | 查看单个节点详情 |
| `get_extraction_guide` | 获取知识提取规则和 JSON 格式说明 |

## Agent Skills

| 技能 | 作用 |
|------|------|
| `read-book` | 读 PDF 书籍，提取概念/规律/现象，入库构建知识图谱 |
| `analyze` | 用知识图谱中的规律分析真实情境，输出因果链和行动建议 |

Skills 提供完整的操作流程指令，agent 加载后自动按步骤执行。MCP 工具提供底层能力。

## 使用流程

### 读书入库

触发 `read-book` skill，或手动：

1. 调用 `gaps()` 查看现有缺口
2. 调用 `pdf_info()` 查看 PDF 分块
3. 调用 `get_extraction_guide()` 获取提取规则
4. Agent 逐块读取 PDF，按规则提取知识
5. 调用 `ingest()` 将提取的 JSON 入库

### 情境分析

触发 `analyze` skill，或手动调用 `analyze()` 工具：

> "我们的SaaS产品试用转付费率很低，用户试用期很活跃但到期就走了"

系统返回相关规律、概念、现象及因果关系网络，agent 据此构建深度分析。

## 数据存储

所有数据存储在 `~/.knowledge-graph/`（本地 JSON 文件，无需数据库）：

```
~/.knowledge-graph/
├── nodes/
│   ├── concepts.json
│   ├── laws.json
│   ├── phenomena.json
│   └── books.json
└── relationships.json
```

## 知识图谱结构

三类节点：
- **Concept（概念）** — 原子级构建块（如：稀缺、激励、损失厌恶）
- **Law（规律）** — 普适因果机制（如：需求定律、前景理论）
- **Phenomenon（现象）** — 规律在现实中的产物（如：公地悲剧、沉没成本谬误）

12 种关系类型连接它们，形成可追溯的因果网络。

## 兼容性

- **MCP Server**: Claude Desktop, Claude Code, claude.ai, Cursor, Windsurf, 及任何 MCP 客户端
- **Agent Skills**: Claude Code, Cursor, VS Code Copilot, GitHub Copilot, Gemini CLI, Goose, Roo Code, OpenAI Codex, JetBrains Junie, 及任何支持 [AgentSkills 规范](https://agentskills.io) 的 agent
