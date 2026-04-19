"""
Whisper 直接识别 + TXT 对比纠错 LRC 生成
1. 用 Whisper 识别整首歌
2. 如果有同名 TXT 文件，去除标签行后逐行对比
3. 相似的行用 TXT 原文替换，保证准确性
"""

import whisper
import os
import re
import argparse
from difflib import SequenceMatcher


def load_txt_lyrics(txt_path):
    """加载 TXT 歌词文件，删除所有标签行"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    clean_lines = []
    for line in lines:
        line = line.strip()
        # 跳过空行
        if not line:
            continue
        # 删除所有包含 [] 标签的行
        if '[' in line and ']' in line:
            continue
        clean_lines.append(line)
    
    return clean_lines


def similarity(a, b):
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a, b).ratio()


def align_and_replace(whisper_lines, txt_lines, threshold=0.6):
    """逐行对比，与所有 TXT 行比较取最大相似度"""
    result = []
    
    for w_line in whisper_lines:
        text = w_line['text']
        best_match_idx = -1
        best_similarity = 0
        
        # 与所有 TXT 行比较，取相似度最大的
        for i, txt_line in enumerate(txt_lines):
            sim = similarity(text, txt_line)
            if sim > best_similarity:
                best_similarity = sim
                best_match_idx = i
        
        # 相似度 < 0.18 的直接丢弃（Whisper 幻觉）
        if best_similarity < 0.18:
            print(f"  🗑️ 丢弃: {text} (相似度=0)")
            continue
        
        # 相似度 > 0，用 TXT 原文替换
        result.append({
            'start': w_line['start'],
            'end': w_line['end'],
            'text': txt_lines[best_match_idx],
            'source': 'txt',
            'similarity': best_similarity
        })
    
    return result


def generate_lrc(audio_path, output_lrc_path=None, model_name=None, threshold=0.6):
    print(f"🚀 正在处理: {audio_path}")
    
    # 检查是否有同名 TXT 文件
    txt_path = os.path.splitext(audio_path)[0] + '.txt'
    has_txt = os.path.exists(txt_path)
    
    if has_txt:
        print(f"📄 发现同名 TXT 文件: {txt_path}")
        txt_lines = load_txt_lyrics(txt_path)
        print(f"📄 TXT 歌词共 {len(txt_lines)} 行")
    else:
        txt_lines = []
        print("📄 未发现同名 TXT 文件")
    
    # 自动选择模型：有 TXT 用 base，否则用 medium
    if model_name is None:
        model_name = 'base' if has_txt else 'medium'
        print(f"🎯 自动选择模型: {model_name}")
    
    # 加载 Whisper 模型
    print("📦 正在加载 Whisper 模型...")
    model = whisper.load_model(model_name)
    print("✅ 模型加载完成")
    
    # 识别整首歌
    print("🎤 正在识别音频...")
    result = model.transcribe(audio_path, language='zh', fp16=False)
    
    # 收集识别结果
    whisper_lines = []
    for segment in result['segments']:
        text = segment['text'].strip()
        no_speech_prob = segment.get('no_speech_prob', 0)
        
        # 丢弃 no_speech_prob 过高且文字很短的片段（大概率误识别或哼唱）
        if no_speech_prob > 0.6 and len(text) < 5:
            print(f"  ⏭️ 跳过: {text} (no_speech_prob={no_speech_prob:.2f})")
            continue
        
        if len(text) > 1:
            whisper_lines.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': text
            })
    
    print(f"🎤 Whisper 识别到 {len(whisper_lines)} 行")
    
    # 对比纠错
    if has_txt and txt_lines:
        print("🔄 正在对比 TXT 文件进行纠错...")
        aligned = align_and_replace(whisper_lines, txt_lines, threshold)
        
        # 统计
        txt_replaced = sum(1 for x in aligned if x['source'] == 'txt')
        whisper_kept = sum(1 for x in aligned if x['source'] == 'whisper')
        print(f"✅ 纠错完成: TXT 替换 {txt_replaced} 行, Whisper 保留 {whisper_kept} 行")
    else:
        aligned = [{'start': x['start'], 'end': x['end'], 'text': x['text'], 'source': 'whisper', 'similarity': 1.0} 
                   for x in whisper_lines]
    
    # 生成 LRC
    print("📝 生成 LRC 文件...")
    lrc_lines = []
    
    for item in aligned:
        lrc_line = f"[{format_time(item['start'])}]{item['text']}"
        lrc_lines.append(lrc_line)
        
        # 标记来源
        marker = "📄" if item['source'] == 'txt' else "🎤"
        sim_info = f"(相似度: {item['similarity']:.2f})" if item['similarity'] < 0.95 else ""
        print(f"  {marker} {lrc_line} {sim_info}")
    
    # 保存
    if lrc_lines:
        with open(output_lrc_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lrc_lines))
        print(f"\n💾 LRC 文件已保存至: {output_lrc_path}")
        print(f"📊 共生成 {len(lrc_lines)} 行歌词")
    else:
        print("⚠️ 未识别到有效歌词")


def format_time(seconds):
    """将秒数转换为 LRC 时间格式 mm:ss.xx"""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Whisper 识别 + TXT 对比纠错生成 LRC')
    parser.add_argument('audio_path', nargs='?', default='test_song.mp3', help='音频文件路径')
    parser.add_argument('-o', '--output', default=None, help='输出LRC文件路径 (默认: 与输入文件同名)')
    parser.add_argument('-m', '--model', default='base', 
                        choices=['tiny', 'base', 'small', 'medium', 'large'],
                        help='Whisper 模型大小 (默认: base)')
    parser.add_argument('-t', '--threshold', type=float, default=0.6, 
                        help='相似度阈值 (默认: 0.6, 低于此值保留 Whisper 结果)')
    
    args = parser.parse_args()
    
    audio_file = args.audio_path
    
    # 自动生成输出文件名（与音乐文件同目录）
    if args.output:
        output_lrc = args.output
    else:
        audio_dir = os.path.dirname(os.path.abspath(audio_file))
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        output_lrc = os.path.join(audio_dir, f"{base_name}.lrc")
    
    if os.path.exists(audio_file):
        generate_lrc(audio_file, output_lrc, args.model, args.threshold)
    else:
        print(f"❌ 文件不存在: {audio_file}")
