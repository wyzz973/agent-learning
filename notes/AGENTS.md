# notes 模块规则

先读../AGENTS.md 与根 COURSE_STATE.json。

问答按日期逐字追加 XML entry，含 q/a/refs 和 HH:MM、Week；不摘要、不改用户原文。复盘由本人填写，不推断已掌握。决策说明为什么与放弃方案，变化新建记录并标记 superseded。仅状态/交接所需资料与用户要求的文档可主动维护。

问答格式如下，同一天只追加：

```markdown
<entry>

**HH:MM · Week NN · 主题**

<q>
用户原文
</q>

<a>
完整回答原文
</a>

<refs>
- 文件或 URL，没有则写 none
</refs>

</entry>
```

CLAUDE.md 链接本文件，不维护另一份规则。
