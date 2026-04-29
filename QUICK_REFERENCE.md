# 快速参考卡 - FFXIV 实时翻译 v2.0

## 🎮 30 秒快速开始

```bash
# 1. 安装
pip install -r requirements.txt

# 2. 运行
python -m app.main

# 3. 设置
   - 选择翻译方案（或离线）
   - 框选对白框 ROI
   - 点击开始
```

## 📋 翻译方案一览

### 方案 1：离线（不翻译）
- ✅ 零配置
- 只显示英文

### 方案 2：Ollama（本地翻译）
- ✅ 完全离线
- ✅ 隐私保护
- 需要：GPU（推荐）

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama serve
```

### 方案 3：DeepSeek（推荐）
- ✅ 翻译质量好
- ✅ 价格便宜
- 需要：API 密钥（免费试用）

🔗 https://api.deepseek.com

### 方案 4：百度翻译
- ✅ 国内快速
- ✅ 免费额度充足
- 需要：APP ID & 密钥

🔗 https://api.fanyi.baidu.com

## 🔧 常用命令

```bash
# 查看 Python 版本
python --version

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows PowerShell）
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 运行程序
python -m app.main

# 测试导入
python -c "import app.main; print('✅')"
```

## 🐛 快速排查

| 问题 | 解决方案 |
|------|--------|
| OCR 识别不准 | 调整 ROI 框选、提高分辨率 |
| 翻译速度慢 | Ollama→升级GPU；API→检查网络 |
| 连接失败 | 检查 Ollama 是否运行；API 密钥是否正确 |
| 程序崩溃 | 重装依赖：`pip install --upgrade -r requirements.txt` |
| 找不到 FF14 窗口 | 游戏必须是窗口化或无边框模式 |

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `README_V2.md` | 完整文档 |
| `GUIDE.md` | 详细使用指南 |
| `DEPLOY_GUIDE.md` | 部署测试 |
| `config.example.json` | 配置示例 |
| `glossary/*.txt` | 术语表 |

## 🎯 UI 操作

```
【目标窗口】
└─ 刷新 → 绑定 → 状态显示

【对白框 ROI】
└─ 框选 → 微调参数

【翻译服务】
├─ 选择类型
├─ 填入凭证
└─ 检查连接

【控制】
└─ 开始 ↔ 暂停 → 清空
```

## 💾 配置保存位置

- **Windows**：`%APPDATA%\FFXIV-Translator\config.json`
- **Linux**：`~/.config/FFXIV-Translator/config.json`
- **macOS**：`~/Library/Application Support/FFXIV-Translator/config.json`

## 📊 性能参数推荐

| 参数 | 推荐值 | 范围 |
|------|--------|------|
| FPS | 3-5 | 1-10 |
| OCR 间隔 | 750ms | 250-5000ms |
| API 超时 | 30s | 10-60s |

## 🚀 高级技巧

### 1. 编辑术语表

编辑 `glossary/` 下的文件：
- `names.txt` - 角色名（不翻译）
- `places.txt` - 地名（不翻译）
- `terms.txt` - 专有名词（不翻译）

### 2. 使用自定义 Ollama 地址

```json
{
  "ollama": {
    "base_url": "http://192.168.1.100:11434",
    "model": "mistral:7b-instruct-q4_K_M"
  }
}
```

### 3. 批量配置多个 API

编辑 `config.json`，同时配置多个 API，运行时动态切换。

## 📱 支持的系统

- ✅ Windows 10/11
- ❌ Linux（需要修改 Windows OCR 部分）
- ❌ macOS（需要修改 Windows OCR 部分）

## 🔗 有用的链接

- [Ollama 官网](https://ollama.ai)
- [DeepSeek API](https://api.deepseek.com)
- [百度翻译](https://api.fanyi.baidu.com)
- [FFXIV 数据库](https://xivapi.com)
- [项目 GitHub](https://github.com/yourusername/ffxiv-translator)

## 💬 常见问题

**Q: 需要 GPU 吗？**
A: 不是必需，但强烈推荐用于 Ollama 本地翻译。

**Q: 数据会被保存吗？**
A: Ollama/离线完全本地；API 方案会发送到服务器。

**Q: 可以用免费 API 吗？**
A: 可以，DeepSeek 和百度翻译都有免费额度。

**Q: 支持实时翻译吗？**
A: 是的，延迟取决于翻译后端和硬件。

**Q: 可以改进识别效果吗？**
A: 补充术语表、提高分辨率、调整 OCR 参数。

## 🛠️ 开发者信息

**项目结构**：
```
app/
├── translate/     # 翻译模块
├── ocr/          # OCR 模块
├── capture/      # 截图模块
├── ui/           # UI 界面
├── glossary/     # 术语管理
├── config.py     # 配置系统
└── main.py       # 入口
```

**主要依赖**：
- PySide6（UI）
- httpx（HTTP）
- Pydantic（配置）
- winsdk（OCR）

## 📞 获取帮助

1. 查看 `GUIDE.md` 详细文档
2. 检查 `DEPLOY_GUIDE.md` 故障排除
3. 阅读 `COMPLETION_REPORT.md` 架构说明
4. 提交 GitHub Issue

---

**版本**：2.0.0  
**最后更新**：2024年  
**许可**：MIT License
