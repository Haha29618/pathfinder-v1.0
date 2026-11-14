
import json
from datetime import date

from core.deepseek_client import chat_completion
from core.job_analyzer import parse_json_response
from core.prompts import ACTION_PLAN_SYSTEM_PROMPT


def determine_plan_mode(days_remaining):
    """
    根据剩余天数选择求职准备模式。
    """

    if days_remaining <= 7:
        return "紧急准备"
    elif days_remaining <= 30:
        return "短期强化"
    elif days_remaining <= 90:
        return "系统提升"
    else:
        return "长期发展"


def generate_action_plan(
    job_profile,
    personal_profile,
    match_report,
    target_date
):
    """
    阶段四：个性化求职行动规划

    输入：
        job_profile：Payload_1
        personal_profile：Payload_2
        match_report：Payload_3
        target_date：预计投递/面试日期

    输出：
        Payload_4：个性化行动计划
    """

    # 检查输入数据
    for name, value in [
        ("岗位画像", job_profile),
        ("个人能力画像", personal_profile),
        ("匹配诊断报告", match_report)
    ]:
        if not isinstance(value, dict):
            raise ValueError(f"{name}必须是字典")

    # 目标日期可使用YYYY-MM-DD字符串
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    if not isinstance(target_date, date):
        raise ValueError("目标日期格式不正确")

    today = date.today()

    days_remaining = (target_date - today).days

    if days_remaining < 0:
        raise ValueError("目标日期不能早于今天")

    # 由Python确定模式，而不是让模型随意选择
    plan_mode = determine_plan_mode(days_remaining)

    # 构造模型输入
    payload = {
        "today": today.isoformat(),
        "target_date": target_date.isoformat(),
        "days_remaining": days_remaining,
        "plan_mode": plan_mode,
        "Payload_1": job_profile,
        "Payload_2": personal_profile,
        "Payload_3": match_report
    }

    messages = [
        {
            "role": "system",
            "content": ACTION_PLAN_SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": (
                "请根据以下数据制定求职行动计划：\n"
                + json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2
                )
            )
        }
    ]

    raw_result = chat_completion(
        messages=messages,
        temperature=0.2,
        max_tokens=4500
    )

    result = parse_json_response(raw_result)

    required_fields = [
        "plan_mode",
        "days_remaining",
        "primary_goal",
        "strategy",
        "priority_tasks",
        "schedule",
        "clarification_before_actions",
        "risks_and_notes",
        "summary"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"行动计划缺少字段：{field}"
            )

    # 检查模型是否遵守时间规则
    if result["plan_mode"] != plan_mode:
        raise ValueError("模型返回的计划模式不正确")

    if result["days_remaining"] != days_remaining:
        raise ValueError("模型返回的剩余天数不正确")

    tasks = result["priority_tasks"]
    schedule = result["schedule"]

    if not isinstance(tasks, list) or not 3 <= len(tasks) <= 5:
        raise ValueError("核心任务数量应为3至5项")

    if not isinstance(schedule, list) or not schedule:
        raise ValueError("时间安排不能为空")

    valid_categories = {
        "表达优化", "信息补充",
        "技能提升", "项目实践", "面试准备"
    }

    valid_priorities = {"高", "中", "低"}

    valid_indices = set(
        range(
            1,
            len(job_profile.get("core_competencies", [])) + 1
        )
    )

    task_ids = []

    for task in tasks:

        task_id = task.get("task_id")

        if not isinstance(task_id, str) or not task_id:
            raise ValueError("任务编号无效")

        task_ids.append(task_id)

        if task.get("category") not in valid_categories:
            raise ValueError("任务类别不正确")

        if task.get("priority") not in valid_priorities:
            raise ValueError("任务优先级不正确")

        hours = task.get("estimated_hours")

        if type(hours) is not int or hours <= 0:
            raise ValueError("预计任务耗时必须为正整数")

        indices = task.get("related_requirement_indices")

        if not isinstance(indices, list):
            raise ValueError("关联岗位编号必须是列表")

        if any(
            type(i) is not int or i not in valid_indices
            for i in indices
        ):
            raise ValueError("任务关联了不存在的岗位要求")

        if not isinstance(task.get("action_steps"), list):
            raise ValueError("任务步骤必须是列表")

        for field in [
            "title", "reason",
            "deliverable", "completion_standard"
        ]:
            if not isinstance(task.get(field), str) or not task[field].strip():
                raise ValueError(f"任务缺少有效字段：{field}")

    if len(task_ids) != len(set(task_ids)):
        raise ValueError("任务编号出现重复")

    # 检查时间安排中的任务编号
    for item in schedule:

        if not isinstance(item, dict):
            raise ValueError("时间安排格式错误")

        if not isinstance(item.get("task_ids"), list):
            raise ValueError("时间安排缺少任务列表")

        for task_id in item["task_ids"]:
            if task_id not in task_ids:
                raise ValueError(
                    f"时间安排引用了不存在的任务：{task_id}"
                )

    # 增加程序确定的日期信息
    result["created_date"] = today.isoformat()
    result["target_date"] = target_date.isoformat()

    return result
