# Seewo 班牌机器人

> [!WARNING]
> 该项目正在开发中，请勿用于学习环境，否则可能会带来严重后果！

## 介绍
Seewo 班牌机器人是一个用于「希沃云班」微信小程序或「希沃魔方」APP的聊天机器人。

## 功能
该程序利用「希沃统一服务平台」的相关API实现「希沃云班」的「亲情留言」以及相关功能，已实现的有：

- 微信二维码登录
- 留言接收
- AI 智能回复（基于 DeepSeek API）
- 联网搜索增强回复
- 图片生成功能（基于 Doubao-Seedream-4.5 API）

## 使用指南

### 1. 环境准备
确保你已添加至少一个学校和学生，并拥有**完整**的 Python **3.10+** 环境。

### 2. 安装依赖
若没有所需依赖库，则运行：

```bash
pip3 install requests numpy Pillow transformers beautifulsoup4 requests_toolbelt
```

### 3. 配置 API 密钥
客制化你的代码：

- 在 `main.py` 第 221 行填入自己的 DeepSeek API 密钥（可在 [DeepSeek 平台](https://platform.deepseek.com) 中自行获取）
- 在 `main.py` 第 270 行填入自己的豆包 API 密钥（可在 [火山引擎 ARK](https://console.volcengine.com/ark/region:ark+cn-beijing/overview) 中自行获取，本程序调用的是 Doubao-Seedream-4.5，所以务必开通该模型）

> 由于本程序需要计算 DeepSeek 回复的单次价格，必须在 Releases 中下载该代码（普通用户直接下载压缩包即可）

### 4. 运行程序

```bash
python3 main.py
```

### 5. 登录流程
首次运行会出现二维码，必须使用**微信扫码**登录。如二维码显示不正常，可在文件目录中查看 `qrcode.png` 文件。

### 6. 使用方式
若程序正常运行，将会实时输出最新留言消息：

- 当收到以 `ai ` 开头的留言时，会自动调用 DeepSeek API 进行回复
- 当收到以 `ais ` 开头的留言时，则会先联网搜集信息，再和问题一起发送给 DeepSeek（相当于联网搜索）
- 当收到以 `img ` 或 `image ` 开头的留言时，会自动调用豆包 API 生成图片并回复

## 相关说明

- API 问题详见 [Seewo-API](https://github.com/cmy2008/api-collet/blob/main/seewo/readme.md)
- 本项目基于 [seewo_robot](https://github.com/cmy2008/seewo_robot) 开发，感谢原作者的贡献
- 如有问题，欢迎联系我邮箱 [2581407416@qq.com](mailto:2581407416@qq.com)（本人初三，周末很短，可能来不及看 issues，见谅）
- 如觉得部署太复杂或没有服务器，可联系我邮箱或私信我 B 站账号 [https://space.bilibili.com/1026416198](https://space.bilibili.com/1026416198)