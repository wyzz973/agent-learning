"""可展示的可信教师新进程源码，真实复现提交与检查点之间的失败边界。"""

WORKER_SOURCE = '''import asyncio, json, os, sys
from pathlib import Path
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from instructor.institution import Institution, lin_he

ROOT, RUN, PHASE = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
service = Institution(ROOT, RUN)
reviewer = lin_he()
marker = RUN / 'committed-before-checkpoint.marker'
approval = service.approve(reviewer, 'KB-A-06', 1)
class State(TypedDict):
    receipt: dict
async def publish(state):
    receipt = service.publish(reviewer, 'KB-A-06', 1, 'crash-fixture-03', approval)
    if not marker.exists():
        marker.write_text('服务已提交，图节点尚未返回', encoding='utf-8')
        raise RuntimeError('受控故障：提交与检查点之间结束节点')
    return {'receipt': receipt}
async def main():
    builder = StateGraph(State)
    builder.add_node('publish', publish)
    builder.add_edge(START, 'publish')
    builder.add_edge('publish', END)
    async with AsyncSqliteSaver.from_conn_string(str(RUN / 'workflow.sqlite3')) as saver:
        graph = builder.compile(checkpointer=saver)
        config = {'configurable': {'thread_id': 'same-institution-task'}}
        try:
            result = await graph.ainvoke({'receipt': {}} if PHASE == 'start' else None, config)
            status = 'resumed'
        except RuntimeError:
            if PHASE != 'start':
                raise
            status = 'interrupted_by_failure'
        print(json.dumps({'status': status, 'pid': os.getpid(),
                          'publications': service.publication_count()}))
asyncio.run(main())
'''
