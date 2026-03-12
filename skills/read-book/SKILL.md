---
description: Read a PDF book/article, extract Concepts, Laws, and Phenomena, and update the knowledge graph
argument-hint: <pdf_path>
allowed-tools: [Bash, Read, Write, Agent, Glob, Grep]
---

# Read Book — Knowledge Graph Builder

User input: $ARGUMENTS

**重要：所有 Python 命令使用以下路径：**
```
KGPY=~/.knowledge-graph/.venv/bin/python3
KGLIB=<PLUGIN_DIR>/lib
```
其中 `<PLUGIN_DIR>` 是本插件的安装目录（包含 lib/ 的那个目录）。首次运行时用 `ls` 确认路径。

## 目标

从书中提取三类**尽量少、尽量基本**的知识单元：**基本概念（Concept）**、**基本规律（Law）**、**现象与应用（Phenomenon）**，构建一张可以解释世界运作道理的**跨学科因果网络**。

**数量级参考**：一本 300 页的入门教科书，通常只有 ~20 个 Concept、~10 条 Law、~30 个 Phenomenon。如果你提取得明显多于此，说明标准太松了。

---

## Step 0：查看已有图谱缺口

```bash
~/.knowledge-graph/.venv/bin/python3 <PLUGIN_DIR>/lib/kg_lite.py gaps
```

**带着这些缺口去读书**：优先寻找能填补 ASSUMES 和 partial 缺口的 Law 和 Concept。

---

## Step 1：解析 PDF 获取分块信息

```bash
~/.knowledge-graph/.venv/bin/python3 <PLUGIN_DIR>/lib/kg_lite.py pdf-info "$ARGUMENTS"
```

记录总页数和分块边界。

---

## Step 2：逐块读取并提取知识

用 Read tool 读 PDF，每次 15-20 页。对每个块，**极为审慎地**提取知识。

---

### 核心原则：宁少勿多

**在提取任何节点之前，先问自己三个过滤问题：**

**过滤器 1（针对 Concept）：这是一个无法进一步分解的原子概念吗？**
- 如果可以用图谱中已有的其他概念来定义它 → 不提取，写进父概念的 definition
- 如果它是某个已有概念的组成部分或子类型 → 不提取，写进父概念的 examples
- 如果它是一个政策工具、测量工具、或机构名称 → 不提取
- 如果它只在一条规律中出现 → 不提取，写进那条规律的 mechanism
- 通过的例子：稀缺、产权、激励、价格、机会成本、信息不对称、交易费用、外部性
- 不通过的例子：庇古税（政策工具）、基尼系数（测量工具）、使用权/收益权/转让权（产权的子属性）

**过滤器 2（针对 Law）：这是一个去掉所有情境限定后仍然成立的普适机制吗？**
- 如果去掉情境限定词（最低工资、保险、选举、侵权…）后它就不成立 → 不是 Law，是 Phenomenon
- 如果它可以从图谱中已有的某条 Law 推导出来 → 不是 Law，是 Phenomenon（那条 Law 的应用）
- 如果它描述的是"某政策实施后会发生什么" → 不是 Law，是 Phenomenon
- 如果它是某条基本规律在特定领域的操作化准则 → 不是 Law，是 Phenomenon（category=准则）
- **极端检验**：能否用一句不含任何专有名词的话表达它？能 → 可能是 Law；不能 → 是 Phenomenon
- 通过的例子：需求定律、比较优势原理、科斯定律、边际效用递减、损失厌恶
- 不通过的例子：汉德公式（科斯定律在侵权法的应用准则）、最低工资法事与愿违（需求定律的应用结果）

**过滤器 3（通用）：这个知识点能从已有节点的组合中推导出来吗？**
- 如果两个已有节点 A + B 的组合已经完整解释了这个知识点 → 不提取新节点，建立关系即可

---

### 三类节点的定义

**Concept（基本概念）** — 原子级构建块，~20个/书
- 是对世界中某种客观存在的条件、状态或力量的最简描述
- 即便读者没学过这个学科，也能感受到这个东西的存在
- 在多条不同规律和现象中作为共同的前提条件出现
- 属性：name / definition（准确、简洁）/ domain（列表）/ **layer**（0=生物基础/1=认知机制/2=互动规律）/ examples（2-3个）/ aliases
- **layer 指南**：
  - layer 0：生物/进化层面的概念（基因、自然选择、适应性）
  - layer 1：认知/心理层面的概念（理性、激励、认知偏差、情绪）
  - layer 2：社会互动层面的概念（价格、产权、市场、制度）— 默认值

**Law（基本规律）** — 普适的因果机制，~10条/书
- 陈述"当条件 X 成立时，机制 M 使得结果 Y 发生"
- 在任何满足条件的领域、情境、时代中都成立
- 不能从图谱中其他规律推导出来
- 类比物理学：真正"牛顿定律级别"的规律只有十几条
- 属性：name / statement（一句话）/ mechanism（底层逻辑）/ conditions[] / exceptions[] / predictive_power / domain（列表）

**Phenomenon（现象与应用）** — 规律作用于现实的一切产物，数量最多
- **定义**：当基本规律作用于特定情境时，产生的可观察模式、应用准则或制度安排
- 包含三个子类（category 字段）：
  - **模式**：可观察的社会模式/事件（公地悲剧、逆向选择、道德风险、搭便车）
  - **准则**：基本规律在特定领域的操作化原则（汉德公式、边际成本定价、排放权交易原理）
  - **制度**：人类为应对某种规律/概念而设计的制度安排（专利制度、中央银行制度、有限责任公司）
- 属性：
  - name — 名称
  - description — 可观察描述或操作定义
  - **causal_chain** — **因果链叙事**：用 2-3 句话解释哪些基本规律和概念如何组合产生了这个现象。格式："因为【概念A】存在，【规律X】起作用，在【情境Y】中产生了【结果Z】"。**如果因果链涉及图谱中尚不存在的机制，在末尾标注【待补】并说明缺什么。**
  - **category** — 子类："模式" / "准则" / "制度"
  - **explanatory_depth** — "complete"（因果链中所有概念和规律都在图谱中）/ "partial"（因果链引用了图谱中尚不存在的机制）
  - conditions[] — 触发条件
  - examples[]（现实实例）
  - aliases
  - domain（列表）

---

### 关系类型

```
Law     → Concept     : INVOLVES（这条规律涉及这个概念）
Law     → Concept     : REQUIRES（这个概念是这条规律成立的外部前提）
Law     → Concept     : ASSUMES（这条规律将此概念作为不证自明的公理假设）
Law     → Concept     : PREDICTS（这条规律预测这个概念会发生变化）
Law     → Law         : IMPLIES（A 成立时 B 也成立）
Law     → Law         : CONTRADICTS（A 和 B 对同一现象做出相反预测）
Law     → Law         : GENERALIZES（A 是 B 的一般化，B 是特例）
Concept → Concept     : TYPE_OF（A 是 B 的一种类型）
Concept → Concept     : MEASURES（A 量化/衡量 B）
Law     → Phenomenon  : PRODUCES（这条规律在特定条件下产生这个现象）
Concept → Phenomenon  : ENABLES（这个概念的存在/缺失使该现象得以发生）
Phenomenon → Phenomenon : TRIGGERS（现象 A 引发现象 B）
```

**提取原则：**
- 只提取书中明确说明的关系，不要推断
- 一条关系对应一个事实
- from/to 必须是本次或之前已提取的节点名称
- 每个 Phenomenon **必须**有至少一条 PRODUCES 关系（从哪条 Law 产生的）
- 优先建立 Law→Phenomenon 的 PRODUCES 关系，这是知识图谱最有解释力的连接

**⚠ 关键规则：最近因原则（Proximate Cause）**
> 每条 PRODUCES 关系必须是**最近因**，不是远因。
> 如果 Law A → Phenomenon X 的因果传导需要经过中间机制 B，应写 A→B 和 B→X，而非直接 A→X。

**⚠ 关键规则：单一 Law 不超过 5 个 PRODUCES**
> 如果一条 Law 的 PRODUCES 目标超过 5 个，逐条验证是否违反最近因原则。

**⚠ 关键规则：ASSUMES 标记学科边界**
> 如果某条 Law 的论证中**默认假设了某种人性/行为模式**但未展开论证（如"人是理性的"），提取为 ASSUMES 关系。

**⚠ 关键规则：桥接概念主动提取**
> 以下类型的概念即使书中没有单独定义章节，也应提取为 Concept（它们是跨学科的铰链）：
> - 人性假设类：理性、自利、合作倾向、公平感
> - 信息类：不确定性、风险、信号
> - 结构类：激励、约束、均衡、反馈

---

### 跨书连接（Step 2 中同步进行）

提取时，检查新提取的节点是否与已有图谱中的节点有关系：
- 新 Law 是否 PREDICTS 了已有 ASSUMES 目标 Concept？（填补公理缺口）
- 新 Concept 是否 ENABLES 了已有 partial Phenomenon？（补全因果链）
- 新 Law 是否 IMPLIES/CONTRADICTS/GENERALIZES 已有 Law？

如果找到这样的连接，在 relationships 中一并提取。

---

### 输出 JSON 格式

```json
{
  "book_title": "书名",
  "pages": "1-20",
  "concepts": [
    {
      "name": "损失厌恶",
      "definition": "人对损失的敏感程度大约是对等量收益的两倍——失去100元的痛苦大于获得100元的快乐",
      "domain": ["心理学", "行为经济学"],
      "layer": 1,
      "examples": ["投资者持有亏损股票过久，因为卖出意味着'确认损失'"],
      "aliases": ["loss aversion"]
    }
  ],
  "laws": [ ... ],
  "phenomena": [ ... ],
  "relationships": [ ... ]
}
```

---

## Step 3：写入文件并入库

用 Write tool 将 JSON 写入临时文件：

```
Write tool → /tmp/kg_chunk_N.json
```

然后入库：

```bash
~/.knowledge-graph/.venv/bin/python3 <PLUGIN_DIR>/lib/kg_lite.py ingest /tmp/kg_chunk_N.json
```

每个块入库完成后继续处理下一块。

---

## Step 4：跨书关系发现与缺口填补

全书处理完毕后查看统计：

```bash
~/.knowledge-graph/.venv/bin/python3 <PLUGIN_DIR>/lib/kg_lite.py stats
```

**重点检查**：
1. 新提取的 Law 是否解释了已有 ASSUMES 关系中的 Concept？如果是，添加 PREDICTS 关系。
2. 是否有 partial Phenomenon 可以因为新知识而升级为 complete？如果是，更新 causal_chain 和 explanatory_depth。
3. 新 Law 的 PRODUCES 数量是否超过 5？逐条验证最近因原则。

---

## Step 5：汇总报告

输出：
- 新增 Concept / Law / Phenomenon 数量，以及合并数量
- 新增关系数量
- 本书核心规律（3-5 条）
- 本书核心现象（3-5 个）及其因果链
- **填补的缺口**：哪些 ASSUMES 被解释了，哪些 partial 升级为 complete
- **新发现的缺口**：新增了哪些 ASSUMES，哪些新 Phenomenon 是 partial
