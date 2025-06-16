# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import tempfile
import subprocess
import base64
from typing import Annotated, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import Field

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("交互式反馈 MCP", log_level="ERROR")

def launch_feedback_ui(summary: str, predefinedOptions: list[str] | None = None) -> dict[str, str | list[str]]:
    # 为反馈结果创建一个临时文件
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        # 获取相对于此脚本的feedback_ui.py路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")

        # 作为单独的进程运行feedback_ui.py
        # 注意：uv似乎有一个bug，所以我们需要
        # 传递一堆特殊标志来使其工作
        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--prompt", summary,
            "--output-file", output_file,
            "--predefined-options", "|||".join(predefinedOptions) if predefinedOptions else ""
        ]
        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )
        if result.returncode != 0:
            raise Exception(f"启动反馈UI失败: {result.returncode}")

        # 从临时文件读取结果
        with open(output_file, 'r') as f:
            result_data = json.load(f)
        os.unlink(output_file)
        
        # 处理图片路径，将图片转换为base64
        if 'image_paths' in result_data and result_data['image_paths']:
            image_data = []
            for img_path in result_data['image_paths']:
                if os.path.exists(img_path):
                    try:
                        with open(img_path, 'rb') as img_file:
                            img_content = img_file.read()
                            img_base64 = base64.b64encode(img_content).decode('utf-8')
                            img_filename = os.path.basename(img_path)
                            image_data.append({
                                'filename': img_filename,
                                'content': img_base64,
                                'path': img_path
                            })
                    except Exception as e:
                        print(f"处理图片时出错: {e}")
            
            # 添加图片数据到结果中
            result_data['images'] = image_data
        
        return result_data
    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e

@mcp.tool()
def interactive_feedback(
    message: str = Field(description="向用户提出的具体问题"),
    predefined_options: list = Field(default=None, description="提供给用户选择的预定义选项（可选）"),
) -> Dict[str, str | List[Dict[str, str]]]:
    """向用户请求交互式反馈，支持文本和图片"""
    # 如果没有提供预定义选项，使用默认选项
    predefined_options_list = predefined_options if isinstance(predefined_options, list) else None
    
    # 确保预定义选项列表不为空
    if not predefined_options_list:
        predefined_options_list = [
            "已解决当前问题",
            "进一步优化程序",
            "进一步优化界面",
            "还有一些问题需要修复",           
            "没有修复任何错误",
        ]
    
    result = launch_feedback_ui(message, predefined_options_list)
    
    # 构建返回结果
    response = {
        'interactive_feedback': result.get('interactive_feedback', '')
    }
    
    # 如果有图片，添加到返回结果中
    if 'images' in result and result['images']:
        response['images'] = result['images']
    
    return response

if __name__ == "__main__":
    mcp.run(transport="stdio")
