"""实际准备20个案例环境并核对初始状态；不执行本人函数，不把准备当通关。"""

import asyncio
import json

from instructor.author_course import write_json
from instructor.check import ROOT, load_catalog
from instructor.enterprise_acceptance import prepare


async def main() -> None:
    """检查真实SQLite、MCP和隔离旧绿设施，保存明确的准备范围。"""
    records = []
    for module in load_catalog()["modules"]:
        cases = json.loads((ROOT / module["directory"] / "production-cases.json").read_text())
        for case in cases["cases"]:
            async with asyncio.timeout(45):
                env = await prepare(module["id"], case["id"], None, "阿灯本次岗位")
            try:
                if case["id"] in {"contract_current", "source_changed"}:
                    assert env.service.document(env.principal, "KB-A-01")["version"] == 2
                if case["id"] == "withdrawn_latest":
                    assert env.service.current_preference(env.principal, "style", 20) is None
                if case["id"] == "old_green":
                    assert not env.coding.latest_verified()
                assert "target_status" not in env.facts
                assert env.service.publication_count() == 0
                records.append(
                    {
                        "module": module["id"],
                        "case": case["id"],
                        "prepared": True,
                        "run_dir": str(env.run_dir),
                        "learner_executed": False,
                        "model_calls": 0,
                    }
                )
            finally:
                if env.endpoint:
                    await asyncio.to_thread(env.endpoint.close)
    write_json(
        ROOT / "outputs/enterprise-redesign/fixture-validation.json",
        {
            "scope": "20份真实初始环境；包含真实MCP协商/关闭及Docker旧绿对照，未执行本人入口。",
            "records": records,
        },
    )
    print("20个环境实际准备通过；本人函数和模型均未执行，不登记通关。")


if __name__ == "__main__":
    asyncio.run(main())
