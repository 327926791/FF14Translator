# FFXIV 实时翻译（改进版 v2.0）

这是一个用于 **FF14 过场/对白框英文台词 → 中文** 的本地桌面程序（Windows）。

## ✨ 核心特性

- ✅ **屏幕 ROI 截图** - 框选对白框区域
- ✅ **Windows OCR** - 自动识别英文
- ✅ **多翻译后端支持** ⭐⭐⭐
  - 离线模式（仅识别）
  - **本地 Ollama**（推荐）- 完全离线，支持本地模型
  - **DeepSeek API**（推荐）- 云端翻译，质量好，价格便宜
  - **百度翻译 API** - 国内服务，稳定快速
- ✅ **术语保护** - 人名/地名/专有名词不翻译
- ✅ **自动去重** - 避免重复显示相同台词
- ✅ **配置管理** - 保存用户设置

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 运行程序

```bash
python -m app.main
```

或直接双击 `run.ps1` (PowerShell) / `run.bat` (CMD)

### 3️⃣ 使用流程

1. **选择窗口** - 刷新并绑定 FF14 窗口
2. **框选 ROI** - 选择对白框区域
3. **配置翻译** - 选择翻译方案（可选）
4. **开始** - 点击开始按钮

详细指南见 [GUIDE.md](./GUIDE.md)

## 🎛️ 翻译方案选择

### 方案 1：离线模式（仅显示英文）
- ✅ 完全免费
- ✅ 无需配置
- ❌ 不翻译

### 方案 2：本地 Ollama（推荐用于本地翻译）
- ✅ 完全离线
- ✅ 隐私保护
- ✅ 支持多种模型
- ⚠️ 需要 GPU（推荐 VRAM ≥ 6GB）

**快速设置：**
```bash
# 安装 Ollama: https://ollama.ai
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama serve
# 程序中选择 Ollama，点击检查连接
```

### 方案 3：DeepSeek API（推荐用于云端翻译）
- ✅ 翻译质量高
- ✅ 响应速度快
- ✅ 成本低（¥0.5-2/百万 tokens）
- ✅ 有免费试用额度

**快速设置：**
1. 访问 https://api.deepseek.com
2. 获取免费 API 密钥
3. 程序中粘贴 API 密钥

### 方案 4：百度翻译 API（推荐用于国内）
- ✅ 国内服务，稳定快速
- ✅ 免费额度充足（2M 字符/月）
- ✅ 成本低

**快速设置：**
1. 访问 https://api.fanyi.baidu.com
2. 申请账号并创建应用
3. 程序中填入 APP ID 和密钥

## 📋 项目结构

```
app/
├── main.py                 # 主程序入口
├── config.py              # 配置管理系统 ⭐ 新增
├── capture/
│   ├── screen_capture.py  # 底层截图
│   └── worker.py          # 后台工作线程
├── ocr/
│   └── windows_ocr.py     # Windows 原生 OCR
├── translate/             # 翻译模块（多后端支持）
│   ├── base.py            # 翻译器基类 ⭐ 新增
│   ├── factory.py         # 翻译器工厂 ⭐ 新增
│   ├── ollama.py          # Ollama 实现
│   ├── deepseek.py        # DeepSeek API ⭐ 新增
│   └── baidu.py           # 百度翻译 API ⭐ 新增
├── glossary/
│   └── glossary.py        # 术语表管理
├── ui/
│   ├── main_window_v2.py  # 改进版主窗口 ⭐ 新增
│   └── roi_select.py      # ROI 框选对话框
└── win/
    └── window_finder.py   # 窗口查找
```

## 📦 依赖列表

```
PySide6           # UI 框架
mss               # 屏幕截图
Pillow            # 图像处理
httpx             # HTTP 客户端
rapidfuzz         # 文本相似度
winsdk            # Windows OCR
pydantic>=2.0     # 配置管理 ⭐ 新增
platformdirs      # 跨平台配置目录 ⭐ 新增
```

## 🆕 新增功能（v2.0）

- ⭐ **多翻译后端支持**
  - Ollama（本地）
  - DeepSeek API（云端）
  - 百度翻译（云端）
  - 离线模式

- ⭐ **配置持久化** - 自动保存用户设置

- ⭐ **改进的 UI**
  - 翻译后端动态切换
  - 连接检查功能
  - 快速开始指南
  - API 文档链接

- ⭐ **更好的错误处理** - 详细的错误提示

## 📝 常见问题

**Q: 为什么识别有错字？**
A: Windows OCR 有时会出错，建议：
- 调整 ROI 框选，确保对白框清晰
- 游戏分辨率越高越准确
- 补充术语表以改进翻译

**Q: 翻译速度慢怎么办？**
A: 
- Ollama：升级 GPU
- API：检查网络连接

**Q: 可以离线使用吗？**
A: 可以，选择：
- 离线模式（不翻译）
- Ollama 本地翻译（需要 Ollama 服务）

**Q: 隐私怎么保护？**
A:
- 离线/Ollama：完全本地，无数据上传
- API：数据会发送到官方服务器，遵循其隐私政策

## 🎮 推荐配置

### 最小配置
- CPU: Intel i5 或同等
- RAM: 4GB
- Windows 10/11

### 推荐配置（Ollama 本地翻译）
- CPU: Intel i7 或同等
- GPU: NVIDIA RTX 3060+ （可选，但强烈推荐）
- RAM: 16GB
- VRAM: 6GB+（如果使用 GPU）

### 推荐配置（API 翻译）
- CPU: 任何支持 Python 的 CPU
- RAM: 4GB+
- 网络：稳定互联网连接

## 📚 相关资源

- [Ollama 官网](https://ollama.ai)
- [DeepSeek API 文档](https://api-docs.deepseek.com/zh-cn/)
- [百度翻译 API](https://api.fanyi.baidu.com)
- [PySide6 文档](https://doc.qt.io/qtforpython/)

## 🤝 贡献

欢迎 Fork 和 Pull Request！

## 📜 许可证

MIT License
