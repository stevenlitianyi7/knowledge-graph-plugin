# Knowledge Graph Lite

从书籍中提取因果规律，构建个人知识图谱，用规律分析真实情境。

## 安装

```bash
git clone <repo-url> ~/knowledge-graph-plugin
cd ~/knowledge-graph-plugin
./setup.sh
```

安装过程自动完成：
- 创建 Python 虚拟环境
- 安装依赖（sentence-transformers, PyMuPDF）
- 下载语义模型（首次约 400MB）

数据存储在 `~/.knowledge-graph/`，本地 JSON 文件，无需数据库。

## 使用

在 Claude Code 中打开本项目目录，然后：

### 读书入库

```
/read-book ~/Downloads/某本书.pdf
```

Claude 会逐页读取 PDF，提取核心概念、规律和现象，自动去重后存入知识图谱。

### 情境分析

```
/analyze 我们的SaaS产品试用转付费率很低
```

系统从知识图谱中检索相关规律，构建因果链分析，给出行动建议。

### 其他命令

```bash
# 查看图谱统计
~/.knowledge-graph/.venv/bin/python3 lib/kg_lite.py stats

# 查看知识缺口
~/.knowledge-graph/.venv/bin/python3 lib/kg_lite.py gaps

# 搜索节点
~/.knowledge-graph/.venv/bin/python3 lib/kg_lite.py search "损失厌恶"
```

## 知识图谱结构

三类节点：
- **Concept（概念）** — 原子级构建块（如：稀缺、激励、损失厌恶）
- **Law（规律）** — 普适因果机制（如：需求定律、前景理论）
- **Phenomenon（现象）** — 规律在现实中的产物（如：公地悲剧、沉没成本谬误）

12 种关系类型连接它们，形成可追溯的因果网络。

## 数据格式

知识以 JSON 存储在 `~/.knowledge-graph/`：

```
~/.knowledge-graph/
├── nodes/
│   ├── concepts.json
│   ├── laws.json
│   ├── phenomena.json
│   └── books.json
└── relationships.json
```
