#!/bin/bash
set -e

KG_HOME="$HOME/.knowledge-graph"
VENV="$KG_HOME/.venv"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  Knowledge Graph Lite — 一键安装          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Create data directories
echo "[1/4] 创建数据目录..."
mkdir -p "$KG_HOME/nodes"

for f in nodes/concepts.json nodes/laws.json nodes/phenomena.json nodes/books.json; do
    [ -f "$KG_HOME/$f" ] || echo '{}' > "$KG_HOME/$f"
done
[ -f "$KG_HOME/relationships.json" ] || echo '[]' > "$KG_HOME/relationships.json"

echo "  ✓ $KG_HOME"

# 2. Create venv
echo ""
echo "[2/4] 创建 Python 虚拟环境..."
if [ -d "$VENV" ]; then
    echo "  ✓ 已存在，跳过"
else
    python3 -m venv "$VENV"
    echo "  ✓ $VENV"
fi

# 3. Install dependencies (use CPU-only torch to save ~1.5GB)
echo ""
echo "[3/4] 安装依赖（首次需要几分钟）..."
"$VENV/bin/pip" install --upgrade pip -q
"$VENV/bin/pip" install -q \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r "$SCRIPT_DIR/requirements.txt"
echo "  ✓ 依赖安装完成"

# 4. Pre-download embedding model
echo ""
echo "[4/4] 下载语义模型（首次约 400MB）..."
"$VENV/bin/python3" -c "
import os, sys
cache = os.path.join('$KG_HOME', '.model_cache')
os.makedirs(cache, exist_ok=True)
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', cache_folder=cache)
dim = m.get_sentence_embedding_dimension()
print(f'  ✓ 模型就绪 (维度: {dim})')
"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  安装完成！                                ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║  使用方法：                                ║"
echo "║  1. 在 Claude Code 中打开本项目目录        ║"
echo "║  2. /read-book <PDF路径>  读书入库         ║"
echo "║  3. /analyze <情境描述>   情境分析          ║"
echo "║                                          ║"
echo "║  数据存储: ~/.knowledge-graph/             ║"
echo "╚══════════════════════════════════════════╝"
