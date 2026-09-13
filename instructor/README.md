# 导师工作台

学习者从根README的当前委托进入Notebook。本目录只维护故事、教材与证据，不能变成另一个必读入口。

- catalog.json：雾岛的28项委托、学习目标、材料状态和情景prompt。课程外前置为空。
- state.json：当前任务/cell和玩家证据。机器可运行、本人解释、陌生输入迁移分别记录。
- render_curriculum.py：从目录生成区域地图和world/prompts，`--check`检查一致性。
- check.py：检查情景、任务字段、Notebook格式、代码标签与当前入口。
- validate_notebooks.py：只执行教师setup/demo；本人练习保持本人完成。
- launch.py：打开当前可学习Notebook。
- PEDAGOGY.md：示范、练习、反馈与迁移的教学依据。
- RESEARCH.md：技术机制、官方来源与版本核查。
- qa/：本机逐字问答记录，不发布到公开仓库。

准备一关时，先编写情景、实际prompt、必要Python、完整示范、本人核心实现、真实验收、作品展示与休息点。Notebook完整且验证后才从draft改为ready；planned只代表委托设计。生成地图或prompt不代表完成教材，不把教师运行写成玩家通关。
