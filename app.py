"""PathFinder v0.1: 大学生个性化求职诊断与成长规划系统。

启动命令：streamlit run app.py
本程序仅调用已经编写好的 core/pipeline.py 和 utils/file_parser.py。
"""

import json
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from core.pipeline import STAGE_NAMES, run_pipeline
from utils.file_parser import extract_resume_text, merge_profile_inputs


st.set_page_config(
    page_title="PathFinder 破局者 | v0.1",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PROJECT_DIR = Path(__file__).resolve().parent
TEST_RESULT_FILE = PROJECT_DIR / "pipeline_result.json"

if "pf_result" not in st.session_state:
    st.session_state.pf_result = None
if "pf_stages" not in st.session_state:
    st.session_state.pf_stages = {}
if "pf_result_source" not in st.session_state:
    st.session_state.pf_result_source = ""


def make_markdown_report(data):
    """将五份Payload整理成可下载的Markdown资产包。"""
    job = data["payload_1"]
    person = data["payload_2"]
    match = data["payload_3"]
    plan = data["payload_4"]
    draft = data["payload_5"]
    resume = draft["resume_draft"]

    lines = [
        "# PathFinder v0.1 求职诊断与材料资产包",
        f"目标岗位：{job.get('position_title', '未填写')}",
        f"目标日期：{data.get('target_date', '未填写')}",
        "",
        "## 一、岗位需求画像",
        job.get("job_summary", ""),
        "",
        "### 核心岗位能力",
    ]
    for item in job.get("core_competencies", []):
        lines.append(
            f"- **{item['name']}**（{item.get('priority', '')}；"
            f"{item.get('requirement_source', '')}）："
            f"{item.get('evidence_from_jd', '')}"
        )

    lines += ["", "## 二、个人能力画像", person.get("profile_summary", ""), ""]
    for item in person.get("experiences", []):
        lines.append(f"### {item.get('id', '')} {item.get('name', '')}")
        for action in item.get("actions", []):
            lines.append(f"- {action}")

    lines += ["", "## 三、岗位适配与差距诊断", match.get("overall_summary", ""), ""]
    for item in match.get("matching_results", []):
        lines += [
            f"### {item.get('requirement_index', '')}. {item.get('requirement_name', '')} — {item.get('status', '')}",
            f"- 判断依据：{item.get('reason', '')}",
            f"- 改进建议：{item.get('next_action', '')}",
        ]

    lines += [
        "", "## 四、个性化求职行动计划",
        f"准备模式：{plan.get('plan_mode', '')}；剩余{plan.get('days_remaining', '')}天",
        plan.get("strategy", ""),
    ]
    for task in plan.get("priority_tasks", []):
        lines += [
            "",
            f"### {task.get('task_id', '')} {task.get('title', '')}（{task.get('priority', '')}优先级）",
            f"- 预计耗时：{task.get('estimated_hours', '')}小时",
            f"- 任务原因：{task.get('reason', '')}",
        ]
        for action in task.get("action_steps", []):
            lines.append(f"- 操作：{action}")
        lines += [
            f"- 预期成果：{task.get('deliverable', '')}",
            f"- 完成标准：{task.get('completion_standard', '')}",
        ]

    lines += ["", "## 五、岗位定制简历（待人工核实）", resume.get("professional_summary", "")]
    education = resume.get("education", {})
    lines += [
        "",
        "### 教育背景",
        f"{education.get('school') or '学校待补充'} | "
        f"{education.get('major') or '专业待补充'} | "
        f"{education.get('education_level') or '学历待补充'}",
        "",
        "### 技能",
    ]
    for skill in resume.get("skills", []):
        lines.append(f"- {skill.get('name', '')}：{skill.get('description', '')}")
    lines += ["", "### 项目与实践经历"]
    for experience in resume.get("experiences", []):
        lines.append(f"#### {experience.get('name', '')}")
        for bullet in experience.get("bullet_points", []):
            lines.append(f"- {bullet.get('text', '')}")

    lines += ["", "### 正式使用前需要核实的信息"]
    for item in draft.get("pending_verifications", []):
        lines.append(f"- {item}")
    lines += [
        "",
        "---",
        "本材料由大模型辅助生成，需由用户核对事实，不代表招聘方评估结果。",
    ]
    return "\n".join(lines)


def display_stage(slot, number, name, state):
    label = f"{number}. {name}"
    if state == "running":
        slot.info(f"⏳ {label} · 正在处理")
    elif state == "completed":
        slot.success(f"✅ {label} · 已完成")
    elif state == "failed":
        slot.error(f"❌ {label} · 处理失败")
    else:
        slot.markdown(f"◯ {label} · 待开始")


# 页面标题
st.title("🧭 PathFinder 破局者")
st.caption("v0.1 · 大学生个性化求职诊断与成长规划系统 · 证据驱动诊断 / 个性化行动 / 真实简历优化")
st.divider()

input_col, process_col, result_col = st.columns([1.2, 0.95, 1.85], gap="large")

# 第一栏：输入配置
with input_col:
    st.subheader("① 输入配置区")
    jd_text = st.text_area(
        "目标岗位JD（必填）",
        height=190,
        placeholder="请粘贴岗位名称、岗位职责、任职要求、优先条件等……",
    )
    uploaded_resume = st.file_uploader(
        "上传简历（可选）",
        type=["pdf", "docx"],
        max_upload_size=10,
        help="支持不超过10MB的PDF或DOCX；扫描版PDF暂不支持。",
    )
    free_text = st.text_area(
        "个人经历补充（可与简历同时使用）",
        height=155,
        placeholder="写下课程项目、竞赛、实习、技能，以及你明确不会的技能等……",
    )
    with st.expander("结构化补充（可选）", expanded=False):
        school = st.text_input("学校")
        major = st.text_input("专业及学历")
        skills = st.text_area("补充技能", height=70)
        extra_experiences = st.text_area("补充项目或竞赛", height=70)

    target_date = st.date_input(
        "预计投递 / 面试日期",
        value=date.today() + timedelta(days=14),
        min_value=date.today(),
        help="未确定具体日期时，可以选择预计准备周期的结束日期。",
    )
    st.caption("资料将发送给DeepSeek API分析；建议先使用虚构测试数据，勿上传身份证号、住址等敏感信息。")
    consent = st.checkbox("我了解资料会发送至DeepSeek进行处理")
    run_clicked = st.button("一键生成求职诊断", type="primary", width="stretch")
    load_clicked = st.button(
        "载入已有测试结果（不调用API）",
        width="stretch",
        disabled=not TEST_RESULT_FILE.is_file(),
        help="用于预览此前真实运行保存的pipeline_result.json，不代表本次实时执行。",
    )
    clear_clicked = st.button("清空上次分析结果", width="stretch")

# 第二栏：流程看板
with process_col:
    st.subheader("② 全流程推进看板")
    stages = st.session_state.pf_stages
    completed_count = sum(s == "completed" for s in stages.values())
    progress_view = st.progress(
        completed_count * 20,
        text=f"已完成 {completed_count}/5 个阶段",
    )
    stage_slots = {}
    for step, stage_name in STAGE_NAMES.items():
        stage_slots[step] = st.empty()
        display_stage(stage_slots[step], step, stage_name, stages.get(step, "pending"))
    st.caption("运行时按顺序调用5个处理节点；前一个阶段的输出自动传递到后续阶段。")


# 清空与载入历史结果
if clear_clicked:
    st.session_state.pf_result = None
    st.session_state.pf_stages = {}
    st.session_state.pf_result_source = ""
    st.rerun()

if load_clicked:
    try:
        with TEST_RESULT_FILE.open("r", encoding="utf-8") as f:
            history = json.load(f)
        if not all(f"payload_{i}" in history for i in range(1, 6)):
            raise ValueError("历史文件缺少五阶段结果")
        st.session_state.pf_result = history
        st.session_state.pf_stages = {i: "completed" for i in range(1, 6)}
        st.session_state.pf_result_source = "历史测试结果预览（没有进行新的API调用）"
        st.rerun()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        with input_col:
            st.error(f"载入历史结果失败：{exc}")


# 点击生成：先检查输入，再执行流水线
if run_clicked:
    if len(jd_text.strip()) < 20:
        with input_col:
            st.warning("请先输入至少20字的目标岗位JD。")
    elif not consent:
        with input_col:
            st.warning("请先确认已了解资料将发送至DeepSeek。")
    else:
        st.session_state.pf_result = None
        st.session_state.pf_result_source = ""
        st.session_state.pf_stages = {}
        progress_view.progress(0, text="正在准备输入数据……")
        for step, name in STAGE_NAMES.items():
            display_stage(stage_slots[step], step, name, "pending")

        try:
            resume_text = ""
            if uploaded_resume is not None:
                resume_text = extract_resume_text(
                    uploaded_resume.name, uploaded_resume.getvalue()
                )

            personal_text = merge_profile_inputs(
                resume_text=resume_text,
                free_text=free_text,
                structured_info={
                    "学校": school,
                    "专业及学历": major,
                    "技能": skills,
                    "其他项目与竞赛": extra_experiences,
                },
            )
            if len(personal_text.strip()) < 20:
                raise ValueError("个人资料过短，请补充至少20字的真实经历。")

            def on_progress(step, name, status, payload):
                st.session_state.pf_stages[step] = status
                display_stage(stage_slots[step], step, name, status)
                done = sum(
                    s == "completed"
                    for s in st.session_state.pf_stages.values()
                )
                progress_view.progress(
                    done * 20,
                    text=f"已完成 {done}/5 个阶段"
                    if status != "failed" else f"第{step}阶段发生错误",
                )

            result = run_pipeline(
                jd_text=jd_text,
                personal_text=personal_text,
                target_date=target_date,
                on_progress=on_progress,
            )
            st.session_state.pf_result = result
            st.session_state.pf_result_source = "本次五阶段实时运行结果"
            with input_col:
                st.success("五个阶段全部完成，右侧可查看成果并下载。")

        except Exception as exc:
            with input_col:
                st.error(f"运行未完成：{exc}")
            st.info("已完成阶段的状态仍会保留。请修复错误后再运行，切勿把API Key放进截图或日志。")


# 第三栏：成果工作台
with result_col:
    st.subheader("③ 求职成果工作台")
    result = st.session_state.pf_result
    if result is None:
        st.info("请先填写资料并运行，或载入之前保存的真实测试结果。")
    else:
        st.caption(st.session_state.pf_result_source)
        job = result["payload_1"]
        profile = result["payload_2"]
        matching = result["payload_3"]
        plan = result["payload_4"]
        resume_package = result["payload_5"]
        resume = resume_package["resume_draft"]

        tab_job, tab_profile, tab_gap, tab_plan, tab_resume = st.tabs(
            ["岗位画像", "个人经历", "差距诊断", "行动计划", "定制简历"]
        )

        with tab_job:
            st.markdown(f"**目标岗位：{job.get('position_title', '未填写')}**")
            st.write(job.get("job_summary", ""))
            st.markdown("**核心能力要求**")
            st.dataframe(
                [
                    {
                        "能力": x.get("name", ""),
                        "重要程度": x.get("priority", ""),
                        "要求来源": x.get("requirement_source", ""),
                    }
                    for x in job.get("core_competencies", [])
                ],
                hide_index=True,
                width="stretch",
            )
            with st.expander("查看岗位职责、优先条件和潜在考察点"):
                for heading, items in [
                    ("岗位职责", job.get("responsibilities", [])),
                    ("优先条件", job.get("preferred_conditions", [])),
                    ("潜在考察点（模型推断）", job.get("potential_assessment_points", [])),
                ]:
                    st.markdown(f"**{heading}**")
                    for item in items:
                        st.markdown(f"- {item}")

        with tab_profile:
            st.write(profile.get("profile_summary", ""))
            st.markdown("**个人经历与真实证据**")
            for experience in profile.get("experiences", []):
                with st.expander(f"{experience.get('id', '')} · {experience.get('name', '')}"):
                    for action in experience.get("actions", []):
                        st.markdown(f"- {action}")
                    st.caption("原文：" + experience.get("source_quote", ""))
            st.markdown("**技能证据**")
            st.dataframe(
                [
                    {
                        "技能": x.get("skill", ""),
                        "证据类型": x.get("evidence_type", ""),
                        "关联经历": ", ".join(x.get("experience_ids", [])),
                    }
                    for x in profile.get("skill_evidence", [])
                ],
                hide_index=True,
                width="stretch",
            )

        with tab_gap:
            st.write(matching.get("overall_summary", ""))
            st.markdown("**岗位要求逐项诊断**")
            st.dataframe(
                [
                    {
                        "岗位能力": x.get("requirement_name", ""),
                        "诊断标签": x.get("status", ""),
                        "依据": x.get("reason", ""),
                        "下一步": x.get("next_action", ""),
                    }
                    for x in matching.get("matching_results", [])
                ],
                hide_index=True,
                width="stretch",
            )
            with st.expander("查看需要补充确认的问题"):
                for question in matching.get("clarification_questions", []):
                    st.markdown(f"- {question}")

        with tab_plan:
            st.markdown(
                f"**{plan.get('plan_mode', '')} · 剩余{plan.get('days_remaining', '')}天**"
            )
            st.write(plan.get("strategy", ""))
            st.markdown("**优先行动任务**")
            for task in plan.get("priority_tasks", []):
                with st.expander(
                    f"{task.get('task_id', '')} · {task.get('title', '')} "
                    f"[{task.get('priority', '')}优先级]"
                ):
                    st.caption(f"类别：{task.get('category', '')} | 预计耗时：{task.get('estimated_hours', '')}小时")
                    for action in task.get("action_steps", []):
                        st.markdown(f"- {action}")
                    st.markdown(f"**预期成果：** {task.get('deliverable', '')}")
                    st.markdown(f"**完成标准：** {task.get('completion_standard', '')}")
            st.markdown("**分阶段时间安排**")
            for item in plan.get("schedule", []):
                st.markdown(
                    f"- **{item.get('period', '')}：** {item.get('focus', '')} "
                    f"（{', '.join(item.get('task_ids', []))}）"
                )

        with tab_resume:
            st.warning("以下是待核实的简历草稿，请确认每项描述真实后再用于正式投递。")
            st.markdown("**个人简介**")
            st.write(resume.get("professional_summary", ""))
            edu = resume.get("education", {})
            st.markdown("**教育背景**")
            st.write(
                f"{edu.get('school') or '学校待补充'} · "
                f"{edu.get('major') or '专业待补充'} · "
                f"{edu.get('education_level') or '学历待补充'}"
            )
            st.markdown("**技能**")
            for item in resume.get("skills", []):
                st.markdown(f"- **{item.get('name', '')}：** {item.get('description', '')}")
            st.markdown("**项目与实践经历**")
            for item in resume.get("experiences", []):
                st.markdown(f"**{item.get('name', '')}**")
                for bullet in item.get("bullet_points", []):
                    st.markdown(f"- {bullet.get('text', '')}")
            with st.expander("待核实信息清单"):
                for item in resume_package.get("pending_verifications", []):
                    st.markdown(f"- {item}")

        st.divider()
        st.markdown("**一键导出资产包**")
        st.download_button(
            "下载完整Markdown报告",
            data=make_markdown_report(result),
            file_name="PathFinder_v0.1_求职诊断报告.md",
            mime="text/markdown; charset=utf-8",
            width="stretch",
            on_click="ignore",
        )
        st.download_button(
            "下载五阶段JSON数据",
            data=json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="PathFinder_v0.1_payloads.json",
            mime="application/json",
            width="stretch",
            on_click="ignore",
        )
        st.caption("上述导出文件可能包含个人资料，分享前请检查并删除不必要的隐私信息。")

st.divider()
st.caption("PathFinder v0.1 · 本系统提供求职准备辅助分析，不代表招聘方评价或录用承诺。")
