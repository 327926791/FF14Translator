# 部署和测试指南

## 🔧 环境准备

### 1. Python 环境

```bash
# 检查 Python 版本（需要 3.10+）
python --version

# 创建虚拟环境（可选但推荐）
python -m venv venv

# 激活虚拟环境
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate
```

### 2. 安装依赖

```bash
# 升级 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

## 🧪 测试步骤

### 测试 1：基本导入测试

```bash
python -c "import app.main; print('✅ 导入成功')"
```

预期输出：`✅ 导入成功`

### 测试 2：OCR 模块测试

```python
from app.ocr.windows_ocr import try_create_windows_ocr
ocr = try_create_windows_ocr()
if ocr:
    print("✅ OCR 模块可用")
else:
    print("❌ OCR 模块不可用（需要 Windows OCR 语言包）")
```

### 测试 3：翻译器工厂测试

```python
from app.translate.factory import TranslatorFactory
from app.translate.base import OllamaConfig

# 测试 Ollama
try:
    cfg = OllamaConfig(base_url="http://localhost:11434")
    translator = TranslatorFactory.create(cfg)
    if translator:
        print("✅ Ollama 翻译器创建成功")
        print(f"   健康检查：{translator.health_check()}")
    else:
        print("❌ Ollama 翻译器创建失败")
except Exception as e:
    print(f"❌ 错误：{e}")
```

### 测试 4：DeepSeek 翻译器测试

```python
from app.translate.factory import TranslatorFactory
from app.translate.base import DeepSeekConfig

try:
    cfg = DeepSeekConfig(api_key="YOUR_API_KEY")
    translator = TranslatorFactory.create(cfg)
    if translator:
        print("✅ DeepSeek 翻译器创建成功")
        # 注意：不建议真正调用 API 进行测试，避免费用
    else:
        print("❌ DeepSeek 翻译器创建失败")
except Exception as e:
    print(f"❌ 错误：{e}")
```

### 测试 5：配置系统测试

```python
from app.config import AppConfig, get_config, set_config

# 加载配置
cfg = get_config()
print(f"✅ 配置加载成功")
print(f"   - 翻译类型：{cfg.translator_type}")
print(f"   - 默认 FPS：{cfg.default_fps}")
print(f"   - OCR 间隔：{cfg.default_ocr_interval_ms}ms")

# 修改并保存
cfg.translator_type = "ollama"
cfg.default_fps = 5
cfg.save_to_file()
print("✅ 配置保存成功")
```

### 测试 6：术语表测试

```python
from app.glossary.glossary import Glossary, protect_terms, restore_terms
from pathlib import Path

# 加载术语表
glossary = Glossary.load_from_dir(Path("glossary"))
print(f"✅ 术语表加载成功")
print(f"   - 人名：{len(glossary.names)}")
print(f"   - 地名：{len(glossary.places)}")
print(f"   - 术语：{len(glossary.terms)}")

# 测试保护和恢复
text = "Alphinaud went to Ul'dah to meet the Primals"
protected, mapping = protect_terms(text, glossary.all_terms())
print(f"\n原文：{text}")
print(f"保护：{protected}")

restored = restore_terms(protected, mapping)
print(f"恢复：{restored}")
```

### 测试 7：UI 启动测试

```bash
python -m app.main
```

预期：应该看到一个 GUI 窗口，包含以下部分：
- 左侧：窗口选择、ROI 设置、翻译配置、控制按钮
- 右侧：日志显示区

## 🚀 Ollama 部署测试

### 1. 安装 Ollama

访问 https://ollama.ai 下载安装 Ollama

### 2. 启动 Ollama 服务

```bash
ollama serve
```

### 3. 拉取模型

```bash
# 在新终端窗口中执行

# 推荐模型（快速，7B）
ollama pull qwen2.5:7b-instruct-q4_K_M

# 其他选项
ollama pull qwen2:7b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M
```

### 4. 测试 Ollama API

```bash
# 测试 API 连接
curl http://localhost:11434/api/tags

# 测试翻译功能
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b-instruct-q4_K_M",
    "stream": false,
    "messages": [
      {"role": "system", "content": "Translate to Chinese"},
      {"role": "user", "content": "Hello world"}
    ]
  }'
```

### 5. 程序中验证

在程序中：
1. 选择翻译类型 → "Ollama（本地）"
2. 点击"检查连接"按钮
3. 应该看到成功提示

## 🌐 DeepSeek API 部署测试

### 1. 获取 API 密钥

1. 访问 https://api.deepseek.com
2. 注册账号
3. 生成 API Key

### 2. 测试 API

```bash
# 设置 API 密钥
$env:DEEPSEEK_API_KEY = "sk-xxxxxxxxxxxxxxxx"

# 测试 API 连接
curl -X POST "https://api.deepseek.com/v1/chat/completions" \
  -H "Authorization: Bearer sk-xxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'
```

### 3. Python 测试

```python
from app.translate.deepseek import DeepSeekTranslator
from app.translate.base import DeepSeekConfig

try:
    cfg = DeepSeekConfig(api_key="sk-your-key-here")
    translator = DeepSeekTranslator(cfg)
    
    # 测试翻译
    result = translator.translate("Alphinaud", "Hello friend")
    print(f"翻译结果：{result}")
except Exception as e:
    print(f"错误：{e}")
```

### 4. 程序中验证

在程序中：
1. 选择翻译类型 → "DeepSeek API"
2. 输入 API 密钥
3. 框选 ROI 后开始使用

## 📊 百度翻译 API 部署测试

### 1. 申请账号

1. 访问 https://api.fanyi.baidu.com
2. 注册账号
3. 创建应用获得 APP ID 和密钥

### 2. 测试 API

```python
from app.translate.baidu import BaiduTranslator
from app.translate.base import BaiduConfig

try:
    cfg = BaiduConfig(app_id="your-app-id", secret_key="your-secret-key")
    translator = BaiduTranslator(cfg)
    
    # 测试健康检查
    if translator.health_check():
        print("✅ 百度翻译 API 连接成功")
        
        # 测试翻译
        result = translator.translate("", "Hello world")
        print(f"翻译结果：{result}")
except Exception as e:
    print(f"错误：{e}")
```

### 3. 程序中验证

在程序中：
1. 选择翻译类型 → "百度翻译"
2. 输入 APP ID 和密钥
3. 框选 ROI 后开始使用

## 🐛 故障排除

### 问题 1：导入错误

```
ModuleNotFoundError: No module named 'PySide6'
```

解决方案：
```bash
pip install --upgrade -r requirements.txt
```

### 问题 2：OCR 不可用

```
RuntimeError: Windows OCR engine unavailable
```

解决方案：
- 检查 Windows 版本（需要 10/11）
- 安装英文语言包：Settings → Time & Language → Language
- 重启电脑

### 问题 3：Ollama 连接失败

```
ConnectionError: Failed to connect to http://localhost:11434
```

解决方案：
```bash
# 确保 Ollama 正在运行
ollama serve

# 检查防火墙
# Windows Defender Firewall → Allow an app through firewall
```

### 问题 4：API 认证失败

```
HTTPStatusError: Client error '401 Unauthorized'
```

解决方案：
- 检查 API 密钥是否正确
- 检查 API 密钥是否过期
- 重新生成新的 API 密钥

## 📈 性能测试

### 1. OCR 性能

```python
import time
from PIL import Image
from app.ocr.windows_ocr import try_create_windows_ocr

ocr = try_create_windows_ocr()
if ocr:
    # 创建测试图片
    img = Image.new('RGB', (400, 100), color='white')
    
    start = time.time()
    for _ in range(5):
        result = asyncio.run(ocr.recognize_pil(img))
    elapsed = time.time() - start
    
    print(f"平均 OCR 耗时：{elapsed/5:.2f}s")
```

### 2. 翻译速度

```python
import time
from app.translate.ollama import OllamaTranslator
from app.translate.base import OllamaConfig

cfg = OllamaConfig()
translator = OllamaTranslator(cfg)

start = time.time()
result = translator.translate("Alphinaud", "Hello world")
elapsed = time.time() - start

print(f"翻译耗时：{elapsed:.2f}s")
print(f"结果：{result}")
```

## ✅ 完整验收清单

- [ ] Python 3.10+ 已安装
- [ ] 所有依赖已安装
- [ ] 程序可以启动
- [ ] OCR 功能正常
- [ ] 可以绑定 FF14 窗口
- [ ] 可以框选 ROI
- [ ] 离线模式可用
- [ ] Ollama 连接正常
- [ ] DeepSeek API 密钥有效
- [ ] 百度翻译凭证有效
- [ ] 配置可以保存和加载
- [ ] 术语表可以正确保护
- [ ] UI 界面流畅无卡顿

---

如有问题，请提交 Issue 或查看 GUIDE.md
