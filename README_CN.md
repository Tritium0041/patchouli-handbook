# Patchouli Handbook

[English README](README.md)

Patchouli Handbook 是一个面向 AI Agent 的文件型知识系统。它借鉴了 skill 的渐进式加载思路，但目标比 skill 更厚：skill 更像某个行为的触发器或 SOP，而 handbook 可以承载完整指导书、路由索引、可复用条目、术语表、来源证据、校验和 CRUD 工具。

当一个 Agent 需要的不只是短流程，而是领域原则、判断规则、案例、反模式和可追溯证据时，就适合使用 Patchouli Handbook。它的核心原则是：先读轻入口，再按需展开，而不是一次性把整本资料塞进上下文。

## 能提供什么

- 基于 Markdown 和 `manifest.json` 的稳定本地文件格式。
- 轻量 `entry_skill/SKILL.md`，用于兼容 skill 风格的激活入口。
- 更厚的 `GUIDE.md`，作为复杂任务的使用指导书。
- 分类页和条目页，用于渐进式展开知识。
- 可选的 evidence 页面和 source index，用于来源追溯。
- Python API 和 JSON CLI，用于创建、编辑、校验、查看 handbook。
- 一个完整示例 handbook，展示它在较大知识量下的组织方式。

## 仓库结构

```text
patchouli_handbook/   Python 库和 CLI
docs/                 架构、写作规范和 Agent 使用协议
example/              示例生成结果
tests/                单元测试
pyproject.toml        包元信息和命令入口
```

## 单个 Handbook 的结构

```text
<handbook_dir>/
├── manifest.json
├── GUIDE.md
├── INDEX.md
├── entry_skill/
│   └── SKILL.md
├── categories/
│   └── <category_slug>/
│       ├── CATEGORY.md
│       └── <entry_slug>.md
├── references/
│   ├── glossary.md
│   └── source_index.md
└── evidence/
    └── <source_id>.md
```

## 快速开始

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

支持 Python 3.10+。

创建一个空 handbook：

```bash
patchouli-handbook init \
  --output output/studio-handbook \
  --title "Studio Handbook" \
  --audience "AI agents and studio maintainers"
```

添加分类和条目：

```bash
patchouli-handbook categories create \
  '{"title":"Planning","description":"Scoping, goals, and project framing."}' \
  --handbook output/studio-handbook

patchouli-handbook entries create \
  '{"title":"Scope First","category_slug":"planning","summary":"Decide the scope before choosing tactics."}' \
  --handbook output/studio-handbook

patchouli-handbook validate --handbook output/studio-handbook
```

查看内置示例：

```bash
patchouli-handbook inspect --handbook example/masahiro-sakurai-on-creating-games
patchouli-handbook validate --handbook example/masahiro-sakurai-on-creating-games
```

示例建议从这两个文件开始读：

- `example/masahiro-sakurai-on-creating-games/GUIDE.md`
- `example/masahiro-sakurai-on-creating-games/INDEX.md`

## CLI

常用命令：

```bash
patchouli-handbook structure
patchouli-handbook describe --handbook <handbook_dir>
patchouli-handbook validate --handbook <handbook_dir>
patchouli-handbook categories list --handbook <handbook_dir>
patchouli-handbook entries get <entry_slug> --handbook <handbook_dir>
```

给 Agent 或外部程序使用的单 JSON 操作入口：

```bash
patchouli-handbook apply '{"action":"get_entry","slug":"scope-first"}' --handbook <handbook_dir>
```

`apply` 支持这些动作：

- `describe`
- `validate`
- `list_categories`
- `list_entries`
- `get_category`
- `get_entry`
- `update_book`
- `create_category`
- `update_category`
- `delete_category`
- `create_entry`
- `update_entry`
- `delete_entry`

CLI 失败也会输出 JSON，方便外部系统解析：

```json
{
  "ok": false,
  "error": {
    "type": "KeyError",
    "message": "'Unknown entry: missing-entry'"
  }
}
```

## Python API

```python
from patchouli_handbook import HandbookStore, create_empty_handbook

create_empty_handbook(
    "output/studio-handbook",
    title="Studio Handbook",
    audience="AI agents and studio maintainers",
)

store = HandbookStore("output/studio-handbook")
store.create_category(
    {
        "title": "Planning",
        "description": "Scoping, goals, and project framing.",
    }
)
store.create_entry(
    {
        "title": "Scope First",
        "category_slug": "planning",
        "summary": "Decide the scope before choosing tactics.",
        "use_when": ["The task is broad or under-specified."],
        "do_this": ["Name the goal.", "Name constraints.", "Pick the smallest useful next step."],
        "checklist": ["The scope is explicit.", "The next action is concrete."],
        "anti_patterns": ["Do not choose tactics before defining the target."],
    }
)
print(store.validate().model_dump())
```

## 从来源摘要构建

builder 可以从一类整理好的 source-summary job 目录生成 handbook。输入目录需要包含：

- `channel.json`
- `videos.json`
- `clean/<video_id>.json`

示例：

```bash
export OPENAI_API_KEY=...
patchouli-handbook build \
  --input path/to/channel-job \
  --output output/generated-handbook
```

builder 会写出 `GUIDE.md`、`INDEX.md`、分类页、条目页、references、evidence、`entry_skill/SKILL.md` 和 `manifest.json`。

## 文档

- [Architecture](docs/architecture.md)：文件结构和各层职责。
- [Agent Protocol](docs/agent-protocol.md)：Agent 应该如何渐进式读取 handbook。
- [Minimal Integration Example](docs/integration-example.md)：外部 Agent 或程序接入 handbook 的最小 CLI 调用闭环。
- [Authoring Guide](docs/authoring-guide.md)：如何添加分类、条目、证据和链接。
- [Minimal Template](docs/template-handbook.md)：创建新 handbook 前的规划模板。

## 内置示例

`example/masahiro-sakurai-on-creating-games` 是一个完整生成示例，包含：

- 14 个 categories
- 260 个 entries
- 299 个 evidence pages
- `GUIDE.md` 和兼容 skill 的 `entry_skill/SKILL.md`

这个示例用于展示厚 handbook 在较大知识量下的导航方式和文件组织方式。

## 测试

```bash
pytest
```
