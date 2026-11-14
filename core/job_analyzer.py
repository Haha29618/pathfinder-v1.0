
import json

from core.deepseek_client import chat_completion
from core.prompts import JOB_ANALYSIS_SYSTEM_PROMPT


def parse_json_response(raw_text):
    """提取并解析大模型返回的JSON"""

    text = raw_text.strip()

    # 兼容模型偶尔返回Markdown代码块的情况
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # 提取JSON对象
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("模型没有返回有效JSON")

    data = json.loads(text[start:end + 1])

    if not isinstance(data, dict):
        raise ValueError("返回结果不是JSON对象")

    return data


def analyze_job_description(jd_text):
    """阶段一：岗位需求解构"""

    if not jd_text or len(jd_text.strip()) < 20:
        raise ValueError("请提供完整的岗位JD，至少输入20个字符")

    messages = [
        {
            "role": "system",
            "content": JOB_ANALYSIS_SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": f"请分析以下招聘岗位JD：\n\n{jd_text}"
        }
    ]

    # 调用DeepSeek
    raw_result = chat_completion(
        messages=messages,
        temperature=0.1,
        max_tokens=2500
    )

    # 解析JSON
    result = parse_json_response(raw_result)

    # 检查必要字段
    required_fields = [
        "position_title",
        "job_summary",
        "responsibilities",
        "core_competencies",
        "preferred_conditions",
        "potential_assessment_points",
        "uncertainties"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(f"模型返回结果缺少字段：{field}")

    return result
