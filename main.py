# -*- coding: utf-8 -*-

# TODO: 多学生选择
import os
import threading
import requests
import json
import math
import time
import transformers
from init import *
from login import *
from funcs import *
from stu import *
from msg import *
from upload import *
from yunban import *

# 初始化deepseek tokenizer
tokenizer_dir = os.path.join(os.path.dirname(__file__), "..", "deepseek_v3_tokenizer", "deepseek_v3_tokenizer")
tokenizer = transformers.AutoTokenizer.from_pretrained(
        tokenizer_dir, trust_remote_code=True
        )

def calculate_tokens(text):
    """计算文本的token数"""
    try:
        tokens = tokenizer.encode(text)
        return len(tokens)
    except Exception as e:
        error_msg = str(e)
        log=f"[ERROR] Token计算失败: {error_msg}"
        logw(log)
        print(date()+log)
        return 0

account=acc()
student=stu(account)
stu_msg=msg(account,student)

def upload_file(account: acc,file,type="image/png"):
    up=Upload(account)
    up.upload(file=file,type=type)
    return up.downloadUrl

def send_msg(msg: msg,send: str):
    try:
        # 计算token数并输出
        token_count = calculate_tokens(send)
        print(f"[Token计数] 消息总token数: {token_count}")
        
        # 自动拆分超过200字的消息
        max_length = 199
        if len(send) <= max_length:
            # 消息长度在限制内，直接发送
            print(send)
            stu_msg.send(send, 1)
        else:
            # 消息长度超过限制，拆分发送
            print(f"消息过长({len(send)}字)，正在拆分为{math.ceil(len(send)/max_length)}条消息发送...")
            # 计算拆分数量
            parts = math.ceil(len(send) / max_length)
            for i in range(parts):
                # 截取当前部分
                start = i * max_length
                end = (i + 1) * max_length
                part = send[start:end]
                # 发送当前部分
                print(f"发送第{i+1}/{parts}条消息: {part}")
                stu_msg.send(part, 1)
                # 每条消息之间添加短暂延迟，避免发送过快
                time.sleep(0.5)
    except Exception as e:
        error_msg = str(e)
        log=f"[ERROR] 发送失败: {error_msg}"
        logw(log)
        print(date()+log)

def parse_web_content(html_content):
    """解析网页内容，提取标题和全部文字信息"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取标题
        title = soup.title.string.strip() if soup.title else ""
        
        # 提取全部文字信息，去除多余空格和换行
        all_text = soup.get_text()
        # 清理文本，去除多余的空格和换行
        all_text = ' '.join(all_text.split())
        
        return {
            'title': title,
            'full_text': all_text
        }
    except Exception as e:
        error_msg = str(e)
        log=f"[ERROR] 解析网页内容失败: {error_msg}"
        logw(log)
        print(date()+log)
        return {
            'title': "",
            'full_text': ""
        }

def get_web_content(url):
    """获取网页的完整内容并解析"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)  # 设置10秒超时
        response.raise_for_status()
        
        # 解析网页内容
        return parse_web_content(response.text)
    except Exception as e:
        error_msg = str(e)
        log=f"[ERROR] 获取网页内容失败: {url} - {error_msg}"
        logw(log)
        print(date()+log)
        return {
            'title': "",
            'full_text': ""
        }

def search_web(query):
    """使用必应搜索API获取12条信息，确保获取6个成功拉取的网页"""
    try:
        # 使用必应搜索API，增加count参数以获取更多结果
        search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&count=15"  # 获取更多结果，便于筛选
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(search_url, headers=headers, timeout=None)  # 取消超时限制
        
        # 解析必应搜索结果
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # 查找所有必应搜索结果（根据必应网页结构调整选择器）
        all_results = soup.find_all('li', class_='b_algo')
        
        # 遍历搜索结果，直到获取到6个成功拉取的网页
        for result in all_results:
            if len(results) >= 6:  # 已经获取了6个成功的结果，退出循环
                break
                
            title = result.find('h2')
            content = result.find('div', class_='b_caption')
            if title and content:
                # 提取摘要内容
                abstract = content.find('p')
                # 提取URL
                url_tag = title.find('a')
                if abstract and url_tag:
                    url = url_tag.get('href')
                    # 获取完整网页内容并解析
                    web_data = get_web_content(url)
                    
                    # 检查是否成功获取了网页内容（标题和内容都不为空）
                    if web_data['title'] and web_data['full_text']:
                        results.append({
                            'search_title': title.get_text().strip(),
                            'search_content': abstract.get_text().strip(),
                            'url': url,
                            'web_title': web_data['title'],
                            'web_full_text': web_data['full_text']
                        })
        
        return results
    except Exception as e:
        error_msg = str(e)
        log=f"[ERROR] 搜索失败: {error_msg}"
        logw(log)
        print(date()+log)
        return []

def call_deepseek_api(prompt, enable_search=False):
    """调用DeepSeek API生成回复，根据参数决定是否启用联网搜索"""
    try:
        full_prompt = prompt
        
        # 1. 如果启用搜索，首先进行网络搜索，获取相关信息
        if enable_search:
            search_results = search_web(prompt)
            
            # 构建带有搜索结果的提示词
            if search_results:
                # 将搜索结果格式化为字符串，包含网页标题和完整文字信息
                search_info_parts = []
                for i, r in enumerate(search_results):
                    part = f"[{i+1}] 搜索标题: {r['search_title']}\n"
                    part += f"   搜索摘要: {r['search_content']}\n"
                    part += f"   网页URL: {r['url']}\n"
                    if r['web_title']:
                        part += f"   网页标题: {r['web_title']}\n"
                    if r['web_full_text']:
                        # 取消网页内容长度限制
                        full_text = r['web_full_text']
                        part += f"   网页内容: {full_text}\n"
                    search_info_parts.append(part)
                
                search_info = "\n".join(search_info_parts)
                # 构建完整的提示词，包含搜索结果
                full_prompt = f"根据以下搜索结果和网页内容，回答用户问题：\n\n搜索结果：\n{search_info}\n\n用户问题：{prompt}"
        
        # 2. 调用DeepSeek API
        api_key = ""
        base_url = "https://api.deepseek.com"
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 根据是否启用搜索，调整系统提示词
        if enable_search:
            system_prompt = "你是一个智能助手，用于回复希沃云班的亲情留言。请根据提供的搜索结果和用户的消息生成合适的回复。如果有搜索结果，请基于搜索结果回答；如果没有搜索结果，根据你的知识回答。"
        else:
            system_prompt = "你是一个智能助手，用于回复希沃云班的亲情留言。请根据用户的消息生成合适的回复。"
        
        data = {
            "model": "deepseek-reasoner",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            "stream": False
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=None)  # 取消超时限制
        response.raise_for_status()
        result = response.json()
        
        # 提取消息内容
        message_content = result["choices"][0]["message"]["content"].strip()
        
        # 提取token使用情况
        usage = result.get("usage", {})
        cache_hit_tokens = usage.get("prompt_cache_hit_tokens", 0)
        cache_miss_tokens = usage.get("prompt_cache_miss_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)  # 输出token数
        
        # 返回消息内容和token使用信息
        return {
            "content": message_content,
            "cache_hit_tokens": cache_hit_tokens,
            "cache_miss_tokens": cache_miss_tokens,
            "completion_tokens": completion_tokens
        }
    except Exception as e:
        error_msg = str(e)
        log=f"[ERROR] DeepSeek API调用失败: {error_msg}"
        logw(log)
        print(date()+log)
        return {
            "content": f"抱歉，我暂时无法回复您的消息。错误原因: {error_msg[:100]}...",
            "cache_hit_tokens": 0,
            "cache_miss_tokens": 0,
            "completion_tokens": 0
        }

def call_doubao_image_api(prompt):
    """调用Doubao-Seedream-4.5 API生成图片"""
    try:
        # Doubao API配置
        api_key = ""  
        url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 构建请求数据
        data = {
            "model": "doubao-seedream-4-5-251128",
            "prompt": prompt,
            "size": "2048x2048",  # 总像素值4194304，符合[3686400, 16777216]要求，宽高比1符合[1/16, 16]要求
            "response_format": "url"
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)  # 图片生成可能需要较长时间
        if response.status_code != 200:
            # 获取更详细的错误信息
            error_response = response.text
            try:
                # 尝试解析JSON格式的错误信息
                error_json = json.loads(error_response)
                error_msg = f"{response.status_code} {response.reason}: {json.dumps(error_json, ensure_ascii=False)}"
            except json.JSONDecodeError:
                # 如果不是JSON格式，直接使用文本
                error_msg = f"{response.status_code} {response.reason}: {error_response}"
            log=f"[ERROR] Doubao API HTTP错误: {error_msg}"
            logw(log)
            print(date()+log)
            return {
                "error": f"图片生成失败。错误原因: {error_msg}"
            }
        
        # 提取图片URL
        result = response.json()
        image_url = result["data"][0]["url"]
        
        return {
            "image_url": image_url
        }
    except Exception as e:
        error_msg = str(e)
        log=f"[ERROR] Doubao API调用失败: {error_msg}"
        logw(log)
        print(date()+log)
        return {
            "error": f"图片生成失败。错误原因: {error_msg[:100]}..."
        }

def send_audio(file):
    stu_msg.send(os.path.basename(file),1)
    url=upload_file(account,file)
    stu_msg.send('',3,url,666)

def main():
    # input_thread = threading.Thread(target=user_input_thread, daemon=True)
    # input_thread.start()
    
    last_msg = ' '
    msg_id=0
    get_id=0
    while True:
        time.sleep(1)
        try:
            get_id=stu_msg.get_id(1)
        except Exception as err:
            log="[ERROR] 获取消息ID失败: " + str(err)
            logw(log)
        if msg_id != get_id:
                try:
                    last_msg=stu_msg.get_content(1)
                    msg_id=get_id
                except Exception as err:
                    log="[ERROR] 消息获取失败"
                    logw(log)
                logw(last_msg)
                print(date()+last_msg)
                
                # 关键词拦截逻辑
                sensitive_keywords = ["所长", "厕所", "尹成锋", "尹", "锋"]
                contains_sensitive = any(keyword in last_msg for keyword in sensitive_keywords)
                
                if contains_sensitive:
                    # 发送警告消息
                    warning_msg = "禁止对项目开发者恶搞"
                    send_msg(stu_msg, warning_msg)
                    print(f"[关键词拦截] 检测到敏感关键词，已发送警告: {warning_msg}")
                    # 跳过后续处理
                    continue
                
                # 调用DeepSeek API生成回复并发送，根据前缀决定是否启用搜索
                if last_msg.strip():
                    try:
                        if last_msg.startswith("ais "):
                            # 以"ais "开头，启用联网搜索
                            prompt = last_msg[4:].strip()
                            api_result = call_deepseek_api(prompt, enable_search=True)
                            # 输出缓存命中情况
                            print(f"[缓存命中情况] 命中tokens: {api_result['cache_hit_tokens']}, 未命中tokens: {api_result['cache_miss_tokens']}")
                            # 发送消息
                            send_msg(stu_msg, api_result['content'])
                            # 计算价格
                            cache_hit_cost = api_result['cache_hit_tokens'] / 1000000 * 0.2
                            cache_miss_cost = api_result['cache_miss_tokens'] / 1000000 * 2
                            completion_cost = api_result['completion_tokens'] / 1000000 * 3
                            total_cost = cache_hit_cost + cache_miss_cost + completion_cost
                            # 构建费用信息字符串
                            cost_info = f"[费用计算] 缓存命中费用: {cache_hit_cost:.4f}元, 缓存未命中费用: {cache_miss_cost:.4f}元, 输出费用: {completion_cost:.4f}元, 总费用: {total_cost:.4f}元"
                            # 输出价格信息到控制台
                            print(cost_info)
                            # 发送费用信息给用户
                            send_msg(stu_msg, cost_info)
                        elif last_msg.startswith("ai "):
                            # 以"ai "开头，直接调用API，不启用搜索
                            prompt = last_msg[3:].strip()
                            api_result = call_deepseek_api(prompt, enable_search=False)
                            # 输出缓存命中情况
                            print(f"[缓存命中情况] 命中tokens: {api_result['cache_hit_tokens']}, 未命中tokens: {api_result['cache_miss_tokens']}")
                            # 发送消息
                            send_msg(stu_msg, api_result['content'])
                            # 计算价格
                            cache_hit_cost = api_result['cache_hit_tokens'] / 1000000 * 0.2
                            cache_miss_cost = api_result['cache_miss_tokens'] / 1000000 * 2
                            completion_cost = api_result['completion_tokens'] / 1000000 * 3
                            total_cost = cache_hit_cost + cache_miss_cost + completion_cost
                            # 构建费用信息字符串
                            cost_info = f"[费用计算] 缓存命中费用: {cache_hit_cost:.4f}元, 缓存未命中费用: {cache_miss_cost:.4f}元, 输出费用: {completion_cost:.4f}元, 总费用: {total_cost:.4f}元"
                            # 输出价格信息到控制台
                            print(cost_info)
                            # 发送费用信息给用户
                            send_msg(stu_msg, cost_info)
                        elif last_msg.startswith("img ") or last_msg.startswith("image "):
                            # 以"img "或"image "开头，调用Doubao API生成图片
                            prompt = last_msg[4:].strip() if last_msg.startswith("img ") else last_msg[6:].strip()
                            print(f"[图片生成] 正在生成图片，提示词: {prompt}")
                            # 发送生成中的提示
                            send_msg(stu_msg, "正在生成图片，请稍候...")
                            # 调用Doubao图片生成API
                            api_result = call_doubao_image_api(prompt)
                            # 处理结果
                            if "image_url" in api_result:
                                image_url = api_result["image_url"]
                                print(f"[图片生成] 图片生成成功，URL: {image_url}")
                                # 下载图片到本地
                                try:
                                    import tempfile
                                    # 创建临时文件保存图片
                                    response = requests.get(image_url, timeout=30)
                                    response.raise_for_status()
                                    
                                    # 创建临时文件
                                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                                        temp_file.write(response.content)
                                        temp_file_path = temp_file.name
                                    
                                    print(f"[图片处理] 图片已下载到本地: {temp_file_path}")
                                    
                                    # 上传图片获取URL
                                    uploaded_url = upload_file(account, temp_file_path, type="image/png")
                                    print(f"[图片处理] 图片已上传，URL: {uploaded_url}")
                                    
                                    # 使用type=4发送图片，根据测试这是正确的图片消息类型
                                    # 使用明确的图片配置，避免被识别为贺卡
                                    res_config = json.dumps({"resourceType": "image", "isCard": False})
                                    stu_msg.send("", 4, uploaded_url, resConfig=res_config)
                                    print(f"[图片处理] 使用type=4发送图片成功")
                                    
                                    # 删除本地临时图片
                                    os.remove(temp_file_path)
                                    print(f"[图片处理] 本地临时图片已删除: {temp_file_path}")
                                    
                                    # 发送成功提示
                                    send_msg(stu_msg, "图片生成成功并已发送！")
                                except Exception as e:
                                    error_msg = str(e)
                                    log=f"[ERROR] 图片处理失败: {error_msg}"
                                    logw(log)
                                    print(date()+log)
                                    send_msg(stu_msg, f"图片处理失败。错误原因: {error_msg[:100]}...")
                                    # 确保临时文件被删除
                                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                                        os.remove(temp_file_path)
                            else:
                                # 发送错误信息，区分敏感内容错误
                                error_msg = api_result["error"]
                                if "sensitive" in error_msg.lower():
                                    # 如果是敏感内容错误，发送更明确的提示
                                    send_msg(stu_msg, "图片生成失败，原因：输入内容可能包含敏感信息，请尝试使用其他描述。")
                                else:
                                    send_msg(stu_msg, error_msg)
                    except Exception as e:
                        error_msg = str(e)
                        log=f"[ERROR] 自动回复失败: {error_msg}"
                        logw(log)
                        print(date()+log)
                        send_msg(stu_msg, f"自动回复处理失败。错误原因: {error_msg[:100]}...")
        else:
            last_msg=" "
        if last_msg == '':
            last_msg = ' '
        if last_msg[0] == "/":
            command = last_msg[1:]
            args=command.split(' ')
            match args[0]:
                case "getpass":
                    send_msg(stu_msg,str(getpass(account,student.schoolUid,args[1],args[2])))
                case "发送音乐":
                    if os.path.exists("music")==False:
                        os.mkdir("music")
                    filelist=os.listdir("music")
                    for file in filelist:
                        send_audio("music/"+file)
                case _:
                    send_msg(stu_msg,os.popen(command).read())

if __name__ == "__main__":
    main()