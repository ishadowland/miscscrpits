import csv
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import warnings
import subprocess

warnings.filterwarnings('ignore', category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

def check_url(url):
    try:
        # 分离网络检测和HTTP检测
        parsed = requests.utils.urlparse(url)
        host = parsed.hostname or url.split('//')[-1].split(':')[0]
        
        # 网络层检测
        ping_ok = check_ping(host)
        
        # 应用层检测
        http_ok = False
        status_code = 'N/A'
        start_time = time.time()
        redirect_url = ''
        try:
            response = requests.get(url, timeout=10, verify=False, allow_redirects=False)
            status_code = response.status_code
            http_ok = 200 <= status_code < 500
            # 处理302重定向
            redirect_url = response.headers.get('Location', '') if status_code == 302 else ''
            # 访问重定向地址并获取状态码
            redirect_status_code = ''
            if redirect_url:
                try:
                    redirect_response = requests.get(redirect_url, timeout=10, verify=False, allow_redirects=False)
                    redirect_status_code = redirect_response.status_code
                except Exception:
                    redirect_status_code = '访问失败'
            elapsed = round((time.time()-start_time)*1000, 2)
        except Exception as http_e:
            elapsed = 0
            redirect_status_code = ''

        return [url, 
                '是' if ping_ok else '否',
                status_code,
                elapsed,
                redirect_url,
                redirect_status_code
                ]
    
    except Exception as e:
        return [url, '否', f"解析失败: {str(e)}", 0, '', '']

def check_ping(host):
    try:
        result = subprocess.run(['ping', '-n', '1', '-w', '1000', host],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True)
        return result.returncode == 0
    except Exception:
        return False

def main():
    start_time = time.time()
    input_file = "input.csv"
    output_file = "output.csv"
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        writer = csv.writer(outfile)
        # 写入表头
        writer.writerow(["网址", "ping是否可达", "http响应状态码", "响应时间", "重定向地址", "重定向状态码"])
        
        # 使用csv.reader正确读取URL，支持包含逗号的URL
        reader = csv.reader(infile)
        urls = [row[0].strip() for row in reader if row and row[0].strip()]
        total_urls = len(urls)
        
        # 读取每个URL并显示进度
        for index, url in enumerate(urls, start=1):
            print(f"正在检查第{index}/{total_urls}个URL: {url}")
            result = check_url(url)
            writer.writerow(result)
            ping_status = "可达" if result[1] == "是" else "不可达"
            print(f"已完成第{index}/{total_urls}个URL检查: ping{ping_status}")
    
    # 统计和报告部分
    if total_urls == 0:
        print("没有URL需要检查。")
        return
    
    ping_success_count = 0
    total_response_time = 0.0
    response_count = 0
    
    with open(output_file, 'r', encoding='utf-8') as report_file:
        reader = csv.reader(report_file)
        next(reader)  # 跳过表头
        for row in reader:
            # 统计ping成功数
            if len(row) >= 2 and row[1] == "是":
                ping_success_count += 1
    
    # 计算总耗时
    total_time = time.time() - start_time
    
    # 打印统计报告
    print("\n===== 执行报告 =====")
    print(f"总检查URL数: {total_urls}")
    print(f"ping成功数: {ping_success_count}")
    print(f"ping成功率: {ping_success_count/total_urls*100:.2f}%" if total_urls > 0 else "ping成功率: 0%")
    print(f"总耗时: {total_time:.4f}秒")
    
    # 打印表格形式的结果
    print("\n===== 检查结果详情 =====")
    with open(output_file, 'r', encoding='utf-8') as report_file:
        reader = csv.reader(report_file)
        rows = list(reader)
        if not rows:
            print("没有检查结果数据。")
            return
        
        headers = rows[0]
        headers = ['网址', 'ping是否可达', '状态码/错误', '响应时间(ms)', '重定向地址', '重定向状态码']
        data = []
        for row in rows[1:]:
            # 确保每行有5列，多余截断，不足补空
            fixed_row = row[:6] + [''] * max(0, 6 - len(row))
            data.append(fixed_row)
        
        # 计算每列最大宽度
        # 计算列宽时同时考虑表头和数据
        # 改进后的列宽计算逻辑
        headers = ['网址', 'ping是否可达', '状态码/错误', '响应时间(ms)', '重定向地址', '重定向状态码']
        col_widths = [
            max(len(str(header)), *[len(str(row[i])) for row in data]) 
            for i, header in enumerate(headers)
        ] if data else [15, 8, 15, 12, 30, 15]  # 为6列设置默认列宽
    
        # 打印表头
        header_line = " | ".join(f"{str(header).ljust(width)}" for header, width in zip(headers, col_widths))
        print(header_line)
        
        # 打印分隔线
        separator_line = "-+".join("-" * col_width for col_width in col_widths)
        print(separator_line)
        
        # 打印数据行
        for row in data:
            row_line = " | ".join(f"{str(cell).ljust(width)}" for cell, width in zip(row, col_widths))
            print(row_line)
    print('\n完整检测结果：')
    with open('output.csv', 'r', encoding='utf-8') as f:
        print(f.read())

if __name__ == "__main__":
    main()