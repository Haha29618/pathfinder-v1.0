
import os
import tomllib
from pathlib import Path

import streamlit as st
from openai import OpenAI


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def get_api_key():
    """读取DeepSeek API密钥"""

    # 优先读取环境变量
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if api_key:
        return api_key.strip()

    # 尝试读取Streamlit Secrets
    try:
        if "DEEPSEEK_API_KEY" in st.secrets:
            api_key = st.secrets["DEEPSEEK_API_KEY"]
            if api_key:
                return str(api_key).strip()
    except Exception:
        pass

    # 读取本地TOML配置文件
    secret_path = (
        PROJECT_ROOT / ".streamlit" / "secrets.toml"
    )

    if secret_path.exists():
        with secret_path.open("rb") as f:
            secrets = tomllib.load(f)

        api_key = secrets.get("DEEPSEEK_API_KEY")

        if api_key:
            return str(api_key).strip()

    raise RuntimeError(
        "没有找到DeepSeek API Key，请检查配置文件。"
    )


def get_deepseek_client():
    """创建DeepSeek客户端"""

    client = OpenAI(
        api_key=get_api_key(),
        base_url="https://api.deepseek.com",
        timeout=60.0,
        max_retries=2
    )

    return client


def chat_completion(
    messages,
    model="deepseek-flash",
    temperature=0.2,
    max_tokens=1000
):
    """调用DeepSeek模型并返回文本"""

    client = get_deepseek_client()

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
        extra_body={
            "thinking": {
                "type": "disabled"
            }
        }
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("大模型没有返回有效文本。")

    return content
