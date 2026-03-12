# Knowledge Graph MCP Server

从书籍中提取因果规律，构建个人知识图谱，用规律分析真实情境。

MCP (Model Context Protocol) 服务器，可被 Claude Desktop、Claude Code、claude.ai 及任何支持 MCP 的 agent 调用。

## 安装

```bash
pip install knowledge-graph-mcp
```

或从源码：

```bash
git clone https://github.com/stevenlitianyi7/knowledge-graph-plugin.git
cd knowledge-graph-plugin
pip install -e .
```

## 配置

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

## 提供的工具

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

## 使用流程

### 读书入库

1. 让 agent 调用 `get_extraction_guide` 获取提取规则
2. 调用 `pdf_info` 查看 PDF 分块
3. Agent 逐块读取 PDF，按规则提取知识
4. 调用 `ingest` 将提取的 JSON 入库

### 情境分析

让 agent 调用 `analyze`，输入你遇到的情境：

> "我们的SaaS产品试用转付费率很低，用户试用期很活跃但到期就走了"

系统返回相关规律、概念、现象及因果关系网络，agent 据此构建分析。

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
