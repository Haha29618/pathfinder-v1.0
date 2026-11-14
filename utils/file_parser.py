
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from docx import Document


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def extract_resume_text(filename, file_bytes):
    """
    从PDF或DOCX文件中提取简历文本。

    filename: 文件名称
    file_bytes: 文件的二进制内容
    返回: 提取后的文本
    """

    extension = Path(filename).suffix.lower()

    if extension not in [".pdf", ".docx"]:
        raise ValueError(
            "暂时只支持PDF和DOCX格式的简历"
        )

    if not file_bytes:
        raise ValueError("上传的文件为空")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("文件不能超过10MB")

    text_parts = []

    try:

        # 处理PDF文件
        if extension == ".pdf":

            reader = PdfReader(BytesIO(file_bytes))

            if reader.is_encrypted:
                raise ValueError(
                    "暂不支持加密PDF，请先解除加密"
                )

            if len(reader.pages) > 20:
                raise ValueError(
                    "PDF页数不能超过20页"
                )

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    text_parts.append(page_text)

        # 处理Word文件
        elif extension == ".docx":

            document = Document(BytesIO(file_bytes))

            # 提取普通段落
            for paragraph in document.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(
                        paragraph.text.strip()
                    )

            # 提取表格内容
            for table in document.tables:
                for row in table.rows:

                    cells = [
                        cell.text.strip()
                        for cell in row.cells
                        if cell.text.strip()
                    ]

                    if cells:
                        text_parts.append(
                            " | ".join(cells)
                        )

    except ValueError:
        raise

    except Exception as e:
        raise ValueError(
            f"简历文件解析失败：{type(e).__name__}"
        ) from e

    result = "\n".join(text_parts).strip()

    if not result:
        raise ValueError(
            "没有提取到文本。请检查文件是否为扫描版PDF。"
        )

    return result


def merge_profile_inputs(
    resume_text="",
    free_text="",
    structured_info=None
):
    """
    合并三种个人信息输入方式，
    生成统一的个人资料文本。
    """

    parts = []

    # 上传简历的文本
    if resume_text.strip():
        parts.append(
            "【上传简历内容】\n" + resume_text.strip()
        )

    # 用户补充的自由文本
    if free_text.strip():
        parts.append(
            "【用户补充经历】\n" + free_text.strip()
        )

    # 结构化表单内容
    if structured_info:
        fields = []

        for name, value in structured_info.items():
            if value and str(value).strip():
                fields.append(
                    f"{name}：{value}"
                )

        if fields:
            parts.append(
                "【结构化补充信息】\n"
                + "\n".join(fields)
            )

    if not parts:
        raise ValueError(
            "请至少提供一种个人资料"
        )

    return "\n\n".join(parts)
