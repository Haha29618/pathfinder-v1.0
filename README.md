# PathFinder 破局者 v0.1

大学生个性化求职诊断与成长规划系统。

## 一、项目功能

系统采用五阶段大语言模型自动化流水线：

1. 岗位需求解构
2. 个人经历与能力画像
3. 岗位适配与差距诊断
4. 个性化求职行动规划
5. 定制化简历生成

支持PDF/DOCX简历上传、自由文本输入、
结构化信息补充及Markdown/JSON成果导出。

## 二、技术环境

- Python 3.10+
- Streamlit
- DeepSeek API
- OpenAI兼容Python SDK
- pypdf
- python-docx

## 三、安装依赖

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## 四、配置API

在项目根目录创建：

.streamlit/secrets.toml

按照secrets.toml.example填写自己的DeepSeek API Key。

请勿将真实API Key上传到公开仓库。

## 五、启动程序

streamlit run app.py

默认本地地址：

http://localhost:8501

## 六、使用说明

输入招聘JD、个人经历和目标日期，
点击“一键生成求职诊断”。

系统依次执行五个处理节点，
最终生成岗位分析、差距诊断、
行动计划和定制简历。

## 七、注意事项

本系统生成内容仅供求职准备参考。
所有简历经历及成果必须经用户人工核实。
