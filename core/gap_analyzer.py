
import json

from core.deepseek_client import chat_completion
from core.job_analyzer import parse_json_response
from core.prompts import MATCHING_SYSTEM_PROMPT


ALLOWED_STATUSES = {
    "已有证据",
    "表达待优化",
    "能力待提升",
    "信息待补充"
}


def analyze_job_match(job_profile, personal_profile):
    """
    阶段三：岗位适配与差距诊断

    输入：
        job_profile：Payload_1，岗位画像
        personal_profile：Payload_2，个人能力画像

    输出：
        Payload_3，岗位匹配诊断报告
    """

    if not isinstance(job_profile, dict):
        raise ValueError("岗位画像必须是字典")

    if not isinstance(personal_profile, dict):
        raise ValueError("个人能力画像必须是字典")

    requirements = job_profile.get(
        "core_competencies", []
    )

    experiences = personal_profile.get(
        "experiences", []
    )

    if not isinstance(requirements, list) or not requirements:
        raise ValueError("岗位能力要求不能为空")

    if not isinstance(experiences, list):
        raise ValueError("个人经历格式错误")

    # 为模型准备输入数据
    input_text = (
        "【Payload_1：岗位能力画像】\n"
        + json.dumps(
            job_profile,
            ensure_ascii=False,
            indent=2
        )
        + "\n\n【Payload_2：个人能力证据】\n"
        + json.dumps(
            personal_profile,
            ensure_ascii=False,
            indent=2
        )
    )

    messages = [
        {
            "role": "system",
            "content": MATCHING_SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": input_text
        }
    ]

    # 调用DeepSeek
    raw_result = chat_completion(
        messages=messages,
        temperature=0.1,
        max_tokens=5000
    )

    # 解析大模型返回的JSON
    result = parse_json_response(raw_result)

    # 检查顶层字段
    required_fields = [
        "position_title",
        "matching_results",
        "strengths",
        "priority_actions",
        "clarification_questions",
        "overall_summary"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"诊断结果缺少字段：{field}"
            )

    matches = result["matching_results"]

    if not isinstance(matches, list):
        raise ValueError(
            "matching_results必须是列表"
        )

    # 检查有没有遗漏岗位要求
    if len(matches) != len(requirements):
        raise ValueError(
            f"岗位要求有{len(requirements)}项，"
            f"但模型只分析了{len(matches)}项"
        )

    valid_ids = {
        exp["id"]
        for exp in experiences
        if isinstance(exp, dict) and "id" in exp
    }

    seen_indices = set()

    for item in matches:

        index = item.get("requirement_index")
        status = item.get("status")
        evidence_ids = item.get("evidence_ids")

        if (
            type(index) is not int
            or index < 1
            or index > len(requirements)
        ):
            raise ValueError(
                f"岗位要求编号无效：{index}"
            )

        if index in seen_indices:
            raise ValueError(
                f"岗位要求编号重复：{index}"
            )

        seen_indices.add(index)

        if status not in ALLOWED_STATUSES:
            raise ValueError(
                f"无效的诊断标签：{status}"
            )

        # 检查岗位名称是否一一对应
        expected_name = requirements[index - 1]["name"]

        if item.get("requirement_name") != expected_name:
            raise ValueError(
                f"第{index}项能力名称与原始JD不一致"
            )

        # 检查引用的经历编号
        if not isinstance(evidence_ids, list):
            raise ValueError(
                "evidence_ids必须是列表"
            )

        for exp_id in evidence_ids:
            if exp_id not in valid_ids:
                raise ValueError(
                    f"引用了不存在的经历：{exp_id}"
                )

    # 检查其他数据结构
    for field in [
        "strengths",
        "priority_actions",
        "clarification_questions"
    ]:
        if not isinstance(result[field], list):
            raise ValueError(
                f"{field}必须是列表"
            )

    return result
