# Whisper LRC Generator

使用 OpenAI Whisper 从音频文件自动生成 LRC 歌词文件。

## 功能特点

- Whisper 端到端语音识别，无需 VAD 检测
- 支持同名TXT 歌词对比校正，相似度匹配过滤幻觉片段，模型可用tiny / base
- 如无txt歌词，建议用midium以上模型
- 自动过滤无效片段（no_speech_prob > 0.6 且文字 < 5字）
- 支持命令行参数配置

## 安装依赖

```bash
pip install -r requirements.txt
```

首次运行会自动下载 Whisper 模型。

## 使用方法

### 基本用法

```bash
python song2lrc.py audio.mp3
```

### 指定模型大小

```bash
# tiny / base / small / medium / large
python song2lrc.py audio.mp3 -m small
```

### 指定相似度阈值

```bash
python song2lrc.py audio.mp3 -t 0.6
```

### 指定输出文件

```bash
python song2lrc.py audio.mp3 -o output.lrc
```

### 带 TXT 校正

将同名 TXT 文件（无标签）放在同目录，程序会自动对比校正。

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| audio_path | 音频文件路径 | test_song.mp3 |
| -m, --model | Whisper 模型 | base |
| -t, --threshold | 相似度阈值 | 0.6 |
| -o, --output | 输出 LRC 路径 | 同名.lrc |

## 右键菜单安装

1. 双击 `install_context_menu.reg` 导入注册表
2. 右键音频文件 → "Generate LRC Lyrics"
3. 卸载：运行 `uninstall_context_menu.bat`
