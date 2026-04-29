# FFXIV 实时翻译 - 使用指南

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python -m app.main
```

或者在 Windows 上双击 `run.bat`

---

## 📖 使用步骤

### 第一步：选择游戏窗口

1. 点击 **"刷新"** 按钮
2. 从下拉列表中选择你的 FF14 窗口
3. 点击 **"绑定"** 确认

### 第二步：框选对白框 ROI

1. 点击 **"框选 ROI"** 按钮
2. 在屏幕上拖拽鼠标框选对白框区域（支持对话框、系统文字框等）
3. 松开鼠标确认，或按 **Esc** 取消

### 第三步：配置翻译服务（可选）

根据你的需求选择翻译方案：

#### 选项 1️⃣：离线模式（仅显示英文）
- 选择 **"离线（不翻译）"**
- 程序只会识别并显示英文，不进行翻译

#### 选项 2️⃣：本地 Ollama 翻译（推荐）
> 优点：完全离线、快速、支持本地模型、隐私保护

前置条件：
- 安装 [Ollama](https://ollama.ai)
- 拉取翻译模型

```bash
# 推荐模型（7B，速度快，质量好）
ollama pull qwen2.5:7b-instruct-q4_K_M

# 其他可选模型
ollama pull qwen2:7b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M
ollama pull neural-chat:7b-q4_K_M
```

配置步骤：
1. 启动 Ollama：`ollama serve`（Windows 安装后会自动启动）
2. 程序中选择 **"Ollama（本地）"**
3. 点击 **"检查连接"** 验证
4. 如果连接成功，点击 **"开始"** 开始翻译

#### 选项 3️⃣：DeepSeek API（快速、便宜）
> 优点：云端翻译、质量好、成本低

获取 API 密钥：
1. 访问 https://api.deepseek.com
2. 注册账号
3. 生成 API Key（有免费试用额度）

配置步骤：
1. 程序中选择 **"DeepSeek API"**
2. 将 API 密钥粘贴到 **"API 密钥"** 字段
3. 点击 **"开始"** 开始翻译

价格参考：¥0.5-2 / 百万 tokens（根据模型）

#### 选项 4️⃣：百度翻译 API（稳定、快速）
> 优点：国内服务、稳定性好、免费额度充足

获取凭证：
1. 访问 https://api.fanyi.baidu.com
2. 注册百度账号
3. 申请开发者账号
4. 创建应用获得 **APP ID** 和 **密钥**
5. 免费试用：每月 2M 字符

配置步骤：
1. 程序中选择 **"百度翻译"**
2. 填入 **APP ID** 和 **密钥**
3. 点击 **"开始"** 开始翻译

### 第四步：开始翻译

1. 设置好上述所有配置后，点击 **"开始"** 按钮
2. 程序会开始实时捕获对白框并进行识别/翻译
3. 识别到的台词和翻译结果会显示在右侧日志区域
4. 点击 **"暂停"** 停止捕获
5. 点击 **"清空记录"** 清除日志

---

## 🛠️ 高级设置

### 调整捕获参数

- **捕获 FPS**：屏幕截图频率（1-10）
  - 较低：CPU 占用低，但可能漏掉台词
  - 较高：CPU 占用高，但捕获更及时
  - 推荐：3-5

- **OCR 间隔(ms)**：识别频率（250-5000ms）
  - 较短：频繁识别，反应快但占用 CPU
  - 较长：识别间隔长，省 CPU 但可能漏掉短台词
  - 推荐：750-1000ms

### 术语保护

在项目根目录的 `glossary/` 文件夹中有三个文本文件：

**names.txt** - 角色名字（一行一个）
```
Alphinaud
Alisaie
Urianger
Thancred
```

**places.txt** - 地名和场景（一行一个）
```
Eorzea
The Crystal Tower
Ul'dah
Limsa Lominsa
```

**terms.txt** - 特殊术语（一行一个）
```
Ascian
Echo
Primals
Ethereal
```

这些词汇在翻译时会被保护（替换为占位符），翻译后再恢复，确保专有名词不被错误翻译。

### 保存配置

每次配置好设置后，点击 **"保存配置"** 按钮保存到本地。下次启动程序时会自动加载这些配置。

配置文件位置（Windows）：
```
%APPDATA%\FFXIV-Translator\config.json
```

---

## 💡 常见问题

### Q1：Ollama 连接失败怎么办？
A：
1. 检查 Ollama 是否在运行：`ollama serve`
2. 确认地址是否正确：`http://localhost:11434`
3. 检查防火墙是否阻止
4. 尝试在浏览器访问 `http://localhost:11434`

### Q2：OCR 识别不准确
A：
- 调整 ROI 框选，确保对白框完整
- 游戏分辨率越高，OCR 越准确
- 确保对白框光线充足，没有阴影

### Q3：翻译速度很慢
A：
- Ollama：升级硬件（GPU 支持会快很多）
- DeepSeek/百度：检查网络连接
- 减少 OCR 间隔，但注意 CPU 占用

### Q4：翻译效果不好
A：
- 本地 Ollama：尝试更大的模型（e.g., 13B）
- 完整术语表：补充 names.txt、places.txt、terms.txt
- 不同 API 翻译质量可能不同，尝试对比

### Q5：会保存我的隐私数据吗？
A：
- 本地 Ollama：完全离线，数据不离机器
- DeepSeek/百度：数据会发送到官方服务器，遵循其隐私政策

---

## 📊 翻译方案对比

| 特性 | 离线 | Ollama | DeepSeek | 百度翻译 |
|------|------|--------|----------|---------|
| 离线可用 | ✅ | ✅ | ❌ | ❌ |
| 隐私性 | ✅⭐ | ✅⭐ | ⭐ | ⭐ |
| 翻译质量 | 无 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 速度 | 快 | 中 | 快 | 快 |
| 成本 | 免费 | 免费 | 便宜 | 免费量 |
| 硬件要求 | 低 | 高 | 无 | 无 |
| 配置难度 | 简单 | 中等 | 简单 | 中等 |

---

## 🔧 故障排除

### 程序无法启动

```bash
# 检查 Python 版本
python --version  # 需要 3.10+

# 重新安装依赖
pip install --upgrade -r requirements.txt

# 尝试清除缓存
pip cache purge
```

### OCR 模块加载失败

Windows OCR 依赖系统 OCR 组件。如果报错，可尝试：
1. 检查 Windows 版本（需要 Windows 10/11）
2. 安装语言包（Settings → Time & Language → Language）
3. 重启电脑

---

## 📝 反馈和改进

如果有 Bug 或建议，欢迎提 Issue 或 Pull Request：
https://github.com/yourusername/ffxiv-translator

---

## 📜 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

