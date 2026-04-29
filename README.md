# FFXIV 实时翻译（本地/OCR）

这是一个用于 **FF14 过场/对白框英文台词 → 中文** 的本地桌面程序（Windows），特点：

- 手动点击 **开始/暂停** 才进行识别与翻译
- 绑定游戏窗口后，截取你设置的对白框区域（ROI）
- OCR 识别英文台词，解析为 `说话人：台词`
- 术语保护：说话人名/地名/专有名词尽量不翻译（词表 + 占位符保护）
- 翻译后端可切换：默认走 **本地 Ollama**；也可切换 DeepSeek API（若你有赠送额度）

## 运行（开发模式）

1) 安装 Python（建议 3.10+）

2) 安装依赖

```bash
pip install -r requirements.txt
```

3) 运行

```bash
python -m app.main
```

## 本地翻译（可选：Ollama）

如果你想用本地模型翻译：

1) 安装并启动 Ollama
2) 拉取模型（示例）

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
```

程序里可以配置模型名与地址（默认 `http://localhost:11434`）。

