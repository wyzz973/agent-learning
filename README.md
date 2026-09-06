# Agent 开发学习仓库

> 起始 2026-09-06 ｜ 工作日每天 1 小时 ｜ 12 周约 60 小时

## 先读哪个

| 文件 | 干什么的 |
|---|---|
| [AGENTS.md](AGENTS.md) | 常驻规范：AI 的角色、目录职责、代码与文档规则。**改动前先读这个** |
| [LEARNING_PATH.md](LEARNING_PATH.md) | 12 周路线，每周目标和自检标准 |
| [RESOURCES.md](RESOURCES.md) | 资源清单、七个常见坑、框架选型 |
| [GLOSSARY.md](GLOSSARY.md) | 术语表：大家怎么说 vs 实际是什么 |

## 这个仓库的三条底线

1. **产出物是我的能力，不是代码。** 评判标准是能不能不看资料重写一遍。所以 AI 不写 `weeks/` 下的主练习文件（[理由](notes/decisions/2026-09-06-learning-repo-structure.md)）。
2. **练习和沉淀分开。** `weeks/` 学完即冻结，`src/agentlab/` 跨周演进。冻结的旧代码是能力增长的存档，不回改。
3. **规则要能被执行。** 能机械检查的都进了 `./check.sh`，不靠自觉。

## 开始

```sh
uv sync                                  # 装依赖
cp .env.example .env                     # 填 key，.env 永不进 git
git init && git add -A && git commit -m "chore: bootstrap learning repo"
```

需要两个 key，都有免费额度：
- **模型 API** — DeepSeek（便宜、国内直连、练手够用）或 Anthropic（工具调用最稳）。`DEFAULT_MODEL` 用 `provider:model` 格式，第 3 周学会用 `init_chat_model` 一行切换
- **LangSmith** — https://smith.langchain.com ，第 2 周就接上，它是唯一的调试手段

## 每周怎么开

```sh
mkdir -p weeks/w01-python-foundations
cp templates/week-readme.md weeks/w01-python-foundations/README.md
cp templates/weekly-note.md notes/weekly/w01.md
```

周一到周四写代码，周五跑 `./check.sh` + 补完复盘 + 打 tag：

```sh
./check.sh && git tag w01-done
```

`check.sh` 会检查每周三件事是否齐全：README、可运行的 `.py`、`test_*.py`，以及对应的复盘文件。缺一个就红。
