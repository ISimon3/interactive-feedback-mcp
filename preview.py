#!/usr/bin/env python
# 交互式反馈界面预览脚本
# 此脚本用于快速预览交互式反馈界面的外观和功能

import sys
import argparse
from feedback_ui import feedback_ui

def main():
    """主函数，用于启动预览界面"""
    parser = argparse.ArgumentParser(description="预览交互式反馈界面")
    parser.add_argument("--theme", choices=["light", "dark", "both"], default="both", 
                        help="选择预览的主题：浅色、深色或两者都显示")
    parser.add_argument("--options", action="store_true", default=True, help="显示带预定义选项的界面")
    parser.add_argument("--many-options", action="store_true", default=True, help="显示大量预定义选项")
    parser.add_argument("--no-options", action="store_true", help="不显示预定义选项")
    args = parser.parse_args()
    
    # 如果指定了no-options，则不显示选项
    if args.no_options:
        args.options = False
        args.many_options = False
    
    # 设置示例提示文本
    prompt = "这是一个示例提示文本。您可以在此处看到修改后的界面效果。\n您可以尝试切换主题、选择预定义选项或输入自定义反馈。"
    
    # 设置预定义选项（如果需要）
    predefined_options = None
    if args.options:
        if args.many_options:
            # 创建大量选项用于测试网格布局和滚动区域
            predefined_options = [
                "选项1：我喜欢这个功能",
                "选项2：需要进一步改进",
                "选项3：有一些问题需要修复",
                "选项4：界面设计很好",
                "选项5：功能非常实用",
                "选项6：操作简单直观",
                "选项7：响应速度很快",
                "选项8：与其他工具集成良好",
                "选项9：文档清晰易懂",
                "选项10：安装过程顺利",
                "选项11：配置选项丰富",
                "选项12：自定义程度高",
                "选项13：支持多平台",
                "选项14：资源占用合理",
                "选项15：更新频率适中"
            ]
        else:
            predefined_options = [
                "选项1：我喜欢这个功能",
                "选项2：需要进一步改进",
                "选项3：有一些问题需要修复"
            ]
    
    # 启动界面
    result = feedback_ui(prompt, predefined_options)
    
    # 显示结果
    if result and result["interactive_feedback"]:
        print(f"\n收到的反馈：\n{result['interactive_feedback']}")
        if result.get('image_paths'):
            print(f"\n附带图片：\n{', '.join(result['image_paths'])}")
    else:
        print("\n未收到反馈或用户取消了操作")

if __name__ == "__main__":
    main() 