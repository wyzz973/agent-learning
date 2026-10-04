"""真实HTTP运输的拒绝路径；使用明确的跳过管线替身，不运行本人实现或模型。"""

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_service_cannot_claim_completion_without_owned_components(tmp_path):
    fake_root = tmp_path / "course"
    project = fake_root / "project"
    (project / "artifacts").mkdir(parents=True)
    (project / "artifacts/team-run.json").write_text('{"owner":"learner","data":{}}')
    for name in ["m06_service", "m06_team", "m06_evaluation", "m04_context"]:
        (project / (name + ".py")).write_text("# 只作为依赖存在标记，不含学生实现\n")
    run = fake_root / "outputs/service-check"
    run.mkdir(parents=True)
    # 唯一替身故意跳过所有本人组件，应被服务独立记录拒绝。
    wrapper = """import sys,runpy,types
from pathlib import Path
from unittest.mock import AsyncMock
actual,root,run=map(Path,sys.argv[1:4])
sys.path.insert(0,str(actual/'modules/05-deep-research'))
for name in ['m06_service','m06_team','m06_evaluation']:
    module=types.ModuleType('project.'+name)
    sys.modules['project.'+name]=module
sys.modules['project.m06_service'].handle_research=AsyncMock(return_value={
    'status':'reported','answer':'不能算完成的固定替身','calls':0})
sys.argv=['service','--root',str(root),'--run',str(run),'--mode','learner']
runpy.run_path(str(actual/'modules/06-research-system/local_research_service.py'),run_name='__main__')
"""
    process = subprocess.Popen(
        [sys.executable, "-c", wrapper, str(ROOT), str(fake_root), str(run)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(100):
            if (run / "ready.json").exists():
                break
            if process.poll() is not None:
                raise AssertionError("服务意外退出")
            time.sleep(0.05)
        url = json.loads((run / "ready.json").read_text())["url"]
        request = urllib.request.Request(
            url + "/jobs",
            data=json.dumps({"question": "林禾要求真实运行本人完整管线"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=5) as reply:
            job_id = json.load(reply)["job_id"]
        for _ in range(100):
            with urllib.request.urlopen(url + "/jobs/" + job_id, timeout=5) as reply:
                result = json.load(reply)
            if result["status"] == "failed":
                break
            time.sleep(0.05)
        assert result["status"] == "failed"
        assert result["result"]["error_type"] == "ValueError"
        assert result["attempts"] == 1
    finally:
        process.terminate()
        process.wait(timeout=5)
