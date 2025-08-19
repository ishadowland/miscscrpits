#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nmap扫描与Ollama AI分析工具
自动执行Nmap扫描并将结果发送给本地Ollama LLM进行分析，生成详细的安全分析报告
"""

import subprocess
import sys
import os
import ollama
from xml.etree import ElementTree as ET

# 配置Ollama模型
OLLAMA_MODEL = 'qwen3:8b'

# AI分析提示模板
ANALYSIS_PROMPT = """你是一名顶级的网络安全分析专家。你的任务是分析以下 Nmap 扫描的 XML 输出数据，并生成一份专业的安全评估报告。

Nmap XML 输出数据如下：
{nmap_xml_output}

请根据以上数据，生成一份 Markdown 格式的详细报告，必须包含以下部分：

### 1. 摘要 (Executive Summary)
对目标的整体安全状况进行高度概括的总结，点出最关键的发现。

### 2. 开放端口和服务分析 (Open Ports & Services)
以 Markdown 表格形式列出所有发现的开放端口。表格应包括：端口号、协议、状态、服务名称和已识别的版本号。

### 3. 潜在风险和漏洞评估 (Potential Risks & Vulnerabilities)
- 逐一分析每个开放端口上的服务。
- 根据服务及其版本号，指出任何已知的、潜在的漏洞（例如，"vsftpd 2.3.4 存在已知的后门漏洞"）。
- 评估可能的配置弱点（例如，"开放的 FTP 端口可能允许匿名登录"）。
- 将风险按高、中、低进行初步评级。

### 4. 修复建议 (Remediation Steps)
- 提供具体、可操作的修复建议来解决上述发现的每一个风险。
- 建议应按优先级排序（从最高风险开始）。
- 示例：更新软件版本、应用安全补丁、关闭不必要的端口、加强防火墙规则等。"""


def check_nmap_installed():
    """检查nmap是否已安装"""
    try:
        subprocess.run(['nmap', '--version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_nmap_scan(target):
    """对目标执行Nmap扫描并返回XML输出"""
    try:
        # 使用全面扫描模式(-A)并以XML格式输出结果(-oX -)
        result = subprocess.run(['nmap', '-A', '-oX', '-', target], 
                               capture_output=True, 
                               text=True, 
                               check=True,
                               timeout=300)  # 5分钟超时
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Nmap扫描失败 {target}: {e}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Nmap扫描超时 {target}")
        return None
    except Exception as e:
        print(f"执行Nmap扫描时出错 {target}: {e}")
        return None


def analyze_with_ollama(xml_output, target):
    """将Nmap XML输出发送给Ollama进行分析"""
    try:
        # 构建提示
        prompt = ANALYSIS_PROMPT.format(nmap_xml_output=xml_output)
        print(prompt)
        # 发送请求到Ollama
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
        print(response)
        # 提取生成的报告
        report = response['response']
        
        # 生成报告文件名
        filename = f"report_{target.replace('/', '_').replace('\\', '_')}.md"
        
        # 保存报告
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"已生成报告: {filename}")
        return True
    except Exception as e:
        print(f"与Ollama通信失败: {e}")
        return False


def main():
    """主函数"""
    # 检查nmap是否已安装
    if not check_nmap_installed():
        print("错误: 未找到nmap，请先安装nmap。")
        sys.exit(1)
    
    # 检查targets.txt文件是否存在
    if not os.path.exists('targets.txt'):
        print("错误: 未找到targets.txt文件。请创建该文件并在其中添加扫描目标。")
        sys.exit(1)
    
    # 读取扫描目标
    try:
        with open('targets.txt', 'r', encoding='utf-8') as f:
            targets = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"读取targets.txt文件时出错: {e}")
        sys.exit(1)
    
    # 检查是否有扫描目标
    if not targets:
        print("targets.txt文件中没有找到有效的扫描目标。")
        sys.exit(1)
    
    # 循环处理所有目标
    for target in targets:
        print(f"正在扫描目标: {target}")
        
        # 执行Nmap扫描
        xml_output = run_nmap_scan(target)
        print(xml_output)
        # 检查扫描是否成功
        if xml_output is None:
            print(f"跳过目标 {target} 的分析，因为扫描失败。")
            continue
        
        # 验证XML输出是否有效
        try:
            ET.fromstring(xml_output)
        except ET.ParseError:
            print(f"目标 {target} 的Nmap输出不是有效的XML格式。")
            continue
        
        # 使用Ollama进行分析
        print(f"正在分析目标: {target}")
        if not analyze_with_ollama(xml_output, target):
            print(f"分析目标 {target} 失败。")
            continue
    
    print("所有目标扫描和分析完成。")


if __name__ == "__main__":
    main()