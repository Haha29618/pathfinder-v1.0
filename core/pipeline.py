
from datetime import date

from core.job_analyzer import analyze_job_description
from core.profile_analyzer import analyze_personal_profile
from core.gap_analyzer import analyze_job_match
from core.action_planner import generate_action_plan
from core.resume_generator import generate_tailored_resume


STAGE_NAMES = {
    1: "岗位需求解构",
    2: "个人经历与能力画像",
    3: "岗位适配与差距诊断",
    4: "个性化求职行动规划",
    5: "定制化简历生成"
}


class PipelineError(RuntimeError):
    """流水线执行异常"""
    pass


def run_pipeline(
    jd_text,
    personal_text,
    target_date,
    on_progress=None
):
    """
    PathFinder v0.1 五阶段自动化流水线。

    参数：
        jd_text：招聘岗位JD文本
        personal_text：整合后的个人资料
        target_date：投递或面试目标日期
        on_progress：进度回调函数（可选）

    返回：
        包含五个Payload的完整结果字典
    """

    # 一、输入检查
    if not isinstance(jd_text, str):
        raise ValueError("岗位JD必须是文本")

    if not isinstance(personal_text, str):
        raise ValueError("个人资料必须是文本")

    if len(jd_text.strip()) < 20:
        raise ValueError("岗位JD内容过短")

    if len(personal_text.strip()) < 20:
        raise ValueError("个人资料内容过短")

    # 防止意外提交超长内容，控制API消耗
    if len(jd_text) > 20000:
        raise ValueError("岗位JD不能超过20000字符")

    if len(personal_text) > 30000:
        raise ValueError("个人资料不能超过30000字符")

    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    if not isinstance(target_date, date):
        raise ValueError("目标日期格式不正确")

    if target_date < date.today():
        raise ValueError("目标日期不能早于今天")

    # 二、定义统一的阶段运行函数
    def execute_stage(step, function, *args):

        stage_name = STAGE_NAMES[step]

        # 通知前端：阶段开始
        if on_progress:
            on_progress(
                step, stage_name, "running", None
            )

        try:
            result = function(*args)

        except Exception as e:

            # 通知前端：阶段失败
            if on_progress:
                on_progress(
                    step, stage_name, "failed", None
                )

            raise PipelineError(
                f"第{step}阶段【{stage_name}】执行失败："
                f"{type(e).__name__}: {e}"
            ) from e

        # 通知前端：阶段完成
        if on_progress:
            on_progress(
                step, stage_name, "completed", result
            )

        return result

    # 三、依次执行五个阶段

    # 阶段一：岗位需求解构
    payload_1 = execute_stage(
        1,
        analyze_job_description,
        jd_text
    )

    # 阶段二：个人经历与能力画像
    payload_2 = execute_stage(
        2,
        analyze_personal_profile,
        personal_text
    )

    # 阶段三：岗位适配与差距诊断
    payload_3 = execute_stage(
        3,
        analyze_job_match,
        payload_1,
        payload_2
    )

    # 阶段四：个性化行动规划
    payload_4 = execute_stage(
        4,
        generate_action_plan,
        payload_1,
        payload_2,
        payload_3,
        target_date
    )

    # 阶段五：定制化简历生成
    payload_5 = execute_stage(
        5,
        generate_tailored_resume,
        payload_1,
        payload_2,
        payload_3,
        payload_4
    )

    # 四、汇总最终结果
    final_result = {
        "system": "PathFinder",
        "version": "v0.1",
        "target_date": target_date.isoformat(),
        "payload_1": payload_1,
        "payload_2": payload_2,
        "payload_3": payload_3,
        "payload_4": payload_4,
        "payload_5": payload_5
    }

    return final_result
