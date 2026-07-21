import streamlit as st
import os
import subprocess
import math
import concurrent.futures
import asyncio
import edge_tts
import time
import shutil
import gc
import threading
import queue


# ─────────────────────────────────────────────
# Timer Utility
# ─────────────────────────────────────────────

def format_time(seconds):
    """Format seconds into mm:ss or mm:ss.ms format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 10)
    if mins > 0:
        return f"{mins}:{secs:02d}"
    return f"{secs}.{ms}s"


# Real-time Timer Thread Removed to prevent NoSessionContext errors.


# ─────────────────────────────────────────────
# TTS Voices, Recap Styles, and Emotions
# ─────────────────────────────────────────────

@st.cache_resource
def get_voices():
    return [
        {"id": "v1", "name": "V1 ♂", "gender": "Male"},
        {"id": "v2", "name": "V2 ♀", "gender": "Female"},
        {"id": "v3", "name": "V3 ♂", "gender": "Male"},
        {"id": "v4", "name": "V4 ♂", "gender": "Male"},
        {"id": "v5", "name": "V5 ♂", "gender": "Male"},
        {"id": "v6", "name": "V6 ♀", "gender": "Female"},
        {"id": "v7", "name": "V7 ♂", "gender": "Male"},
        {"id": "v8", "name": "V8 ♀", "gender": "Female"},
        {"id": "v9", "name": "V9 ♂", "gender": "Male"},
        {"id": "v10", "name": "V10 ♀", "gender": "Female"},
        {"id": "v11", "name": "V11 ♀", "gender": "Female"},
        {"id": "v12", "name": "V12 ♂", "gender": "Male"},
        {"id": "v13", "name": "V13 ♀", "gender": "Female"},
        {"id": "v14", "name": "V14 ♂", "gender": "Male"}
    ]

@st.cache_resource
def get_recap_styles():
    return [
        {"id": "Normal", "name": "ပုံမှန်အသံ", "speed": 0, "pitch": 0},
        {"id": "NyoGyi_25", "name": "ကျားကြီး ၁", "speed": 0, "pitch": 25},
        {"id": "NyoGyi_35", "name": "ကျားကြီး ၂", "speed": 0, "pitch": 35},
        {"id": "NyoGyi_45", "name": "ကျားကြီး ၃", "speed": 0, "pitch": 45},
        {"id": "Nilar_40", "name": "နီလာ ချွဲသံ", "speed": 0, "pitch": 40},
        {"id": "Combo_15", "name": "ပေါင်းစပ် ၁၅", "speed": 15, "pitch": 15},
        {"id": "Combo_30", "name": "ပေါင်းစပ် ၃၀", "speed": 30, "pitch": 30},
        {"id": "Combo_50", "name": "ပေါင်းစပ် ၅၀", "speed": 50, "pitch": 50},
        {"id": "Pitch_20", "name": "အသံသေး ၂၀", "speed": 0, "pitch": 20},
        {"id": "Pitch_50", "name": "အသံသေး ၅၀", "speed": 0, "pitch": 50}
    ]

@st.cache_resource
def get_emotions():
    return [
        {"id": "EXCITING", "name": "စိတ်လှုပ်ရှား 🤩", "s": 15, "p": 10},
        {"id": "CALM", "name": "တည်ငြိမ် 😌", "s": -10, "p": -5},
        {"id": "PROFESSIONAL", "name": "သတင်း 💼", "s": 0, "p": -2},
        {"id": "NARRATIVE", "name": "ဇာတ်ကြောင်း 📖", "s": -5, "p": 0},
        {"id": "HAPPY", "name": "ပျော်ရွှင် 😊", "s": 10, "p": 15},
        {"id": "SERIOUS", "name": "လေးနက် 😠", "s": -5, "p": -10},
        {"id": "WHISPER", "name": "တီးတိုး 🤫", "s": -15, "p": -20},
        {"id": "SAD", "name": "ဝမ်းနည်း 😢", "s": -15, "p": -15},
        {"id": "SARCASTIC", "name": "ရွဲ့ပြော 🙄", "s": -10, "p": 5},
        {"id": "ANGRY", "name": "ဒေါသထွက် 🤬", "s": 20, "p": -10},
        {"id": "FEAR", "name": "ကြောက်လန့် 😨", "s": 10, "p": 20}
    ]

VOICES = get_voices()
RECAP_STYLES = get_recap_styles()
EMOTIONS = get_emotions()

st.set_page_config(page_title="Video & Text Processor", layout="wide")


def count_paragraphs(text):
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return paragraphs


# ─────────────────────────────────────────────
# TTS Generation
# ─────────────────────────────────────────────

async def generate_all_tts(paragraphs, audio_dir, voice_id, speed, pitch):
    """Generate TTS for all paragraphs in parallel."""
    tasks = []
    for i, paragraph in enumerate(paragraphs):
        tasks.append(generate_tts_async(paragraph, os.path.join(audio_dir, f"audio_{i}.mp3"), voice_id, speed, pitch))
    await asyncio.gather(*tasks)


VOICE_MAP = {
    "v1": "my-MM-ThihaNeural",
    "v2": "my-MM-NilarNeural",
    "v3": "it-IT-GianniNeural",
    "v4": "en-AU-WilliamMultilingualNeural",
    "v5": "en-US-AndrewMultilingualNeural",
    "v6": "en-US-AvaMultilingualNeural",
    "v7": "en-US-BrianMultilingualNeural",
    "v8": "en-US-EmmaMultilingualNeural",
    "v9": "fr-FR-RemyMultilingualNeural",
    "v10": "fr-FR-VivienneMultilingualNeural",
    "v11": "de-DE-SeraphinaMultilingualNeural",
    "v12": "de-DE-FlorianMultilingualNeural",
    "v13": "pt-BR-ThalitaMultilingualNeural",
    "v14": "ko-KR-HyunsuMultilingualNeural"
}

async def generate_tts_async(text, output_path, voice_id, speed, pitch):
    """Async TTS generation for parallel execution."""
    real_voice = VOICE_MAP.get(voice_id, "my-MM-ThihaNeural")
    rate_str = f"+{speed}%" if speed >= 0 else f"{speed}%"
    pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"{pitch}Hz"
    communicate = edge_tts.Communicate(text, real_voice, rate=rate_str, pitch=pitch_str)
    await communicate.save(output_path)
    return output_path


# ─────────────────────────────────────────────
# Probe Helpers
# ─────────────────────────────────────────────

def get_video_duration(video_path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())


def get_video_resolution(video_path):
    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
           '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', video_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    res = result.stdout.strip().split('x')
    w, h = int(res[0]), int(res[1])
    return w, h


def get_audio_duration(audio_path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())


# ─────────────────────────────────────────────
# Step 1: Split video into segments (video only, no audio)
# ─────────────────────────────────────────────

def split_video(video_path, num_segments, output_dir):
    """Split video into segments using fast copy (instant, no re-encoding).
    Audio is stripped to avoid conflicts."""
    duration = get_video_duration(video_path)
    segment_duration = duration / num_segments
    segments = []
    for i in range(num_segments):
        start_time = i * segment_duration
        output_path = os.path.join(output_dir, f"segment_{i}.mp4")
        cmd = ['ffmpeg', '-y', '-ss', str(start_time), '-t', str(segment_duration),
               '-i', video_path, '-c:v', 'copy', '-an',
               '-avoid_negative_ts', 'make_zero', output_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        segments.append(output_path)
    return segments, segment_duration


# ─────────────────────────────────────────────
# Step 2: Speed-adjust each segment to match TTS audio
# ─────────────────────────────────────────────

def speed_adjust_segment(index, video_segment, audio_path, adjusted_dir):
    """Speed-adjust VIDEO ONLY to match TTS audio duration.
    TTS audio is kept at original speed (no atempo).
    Returns (output_path, audio_dur, target_dur, speed_factor) on success.
    Cleans up the original segment after success."""
    audio_duration = get_audio_duration(audio_path)
    orig_duration = get_video_duration(video_segment)
    output_path = os.path.join(adjusted_dir, f"adjusted_{index}.mp4")

    # Target video duration is rounded up to the nearest 0.5s increment
    # relative to the audio duration (ensuring a buffer of 0 to 0.5s).
    # This prevents audio truncation while keeping the buffer small.
    target_video_duration = math.ceil(audio_duration * 2) / 2
    
    # Ensure the video is at least as long as the audio (handle float precision)
    if target_video_duration < audio_duration:
        target_video_duration = audio_duration
        
    speed_factor = target_video_duration / orig_duration

    # Use a simpler filter complex that only touches video PTS.
    # We map audio directly (1:a) to ensure the TTS audio duration is strictly preserved.
    # We do NOT use -shortest because we want the video to be slightly longer (0-0.5s) than the audio.
    cmd = [
        'ffmpeg', '-y',
        '-i', video_segment,
        '-i', audio_path,
        '-filter_complex', f"[0:v]setpts={speed_factor}*PTS[v]",
        '-map', '[v]',
        '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'ultrafast',
        '-c:a', 'aac',
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0 and os.path.exists(output_path):
        if os.path.exists(video_segment):
            os.remove(video_segment)
        return (output_path, audio_duration, target_video_duration, speed_factor)
    else:
        raise Exception(f"Speed adjust failed for segment {index}: {result.stderr}")


# ─────────────────────────────────────────────
# Step 3: Apply cycle repeat + zoom to a single segment
# ─────────────────────────────────────────────

def build_cycle_filter(video_path, segment_duration,
                       play_dur, freeze1_dur, freeze2_dur,
                       freeze1_zoom, freeze2_zoom, zoom_dur):
    """Build FFmpeg filter complex for cycle repeat on a segment.
    Cycle repeat is limited to segment_duration to prevent exceeding it."""
    fps = 24
    cycle_duration = play_dur + freeze1_dur + freeze2_dur
    num_cycles = math.ceil(segment_duration / cycle_duration)

    # Use original resolution
    width, height = get_video_resolution(video_path)
    res_str = f"{width}x{height}"

    def make_zoom_filter(zoom_dur, total_dur, zoom_type):
        total_frames = max(int(total_dur * fps), 1)
        zoom_frames = max(int(zoom_dur * fps), 1)
        # Cap zoom_frames at total_frames to avoid overflow
        z_frames = min(zoom_frames, total_frames)
        
        if zoom_type == "Zoom In":
            # Zoom from 1.0 to 1.15 over z_frames, then stay at 1.15
            return (f"zoompan=z='if(lte(on,{z_frames}),min(1+0.15*on/{z_frames},1.15),1.15)':"
                    f"d={total_frames}:s={res_str}:fps={fps}")
        elif zoom_type == "Zoom Out":
            # Zoom from 1.15 to 1.0 over z_frames, then stay at 1.0
            return (f"zoompan=z='if(lte(on,{z_frames}),max(1.15-0.15*on/{z_frames},1.0),1.0)':"
                    f"d={total_frames}:s={res_str}:fps={fps}")
        return None

    f1_z = make_zoom_filter(zoom_dur, freeze1_dur, freeze1_zoom) if freeze1_zoom != "None" else None
    f2_z = make_zoom_filter(zoom_dur, freeze2_dur, freeze2_zoom) if freeze2_zoom != "None" else None

    filter_parts = []
    concat_inputs = []

    for i in range(num_cycles):
        curr = i * cycle_duration

        # Play section — cap at segment_duration to prevent exceeding
        play_end = min(curr + play_dur, segment_duration)
        filter_parts.append(
            f"[0:v]trim=start={curr}:end={play_end},"
            f"setpts=PTS-STARTPTS[vplay_{i}];")
        concat_inputs.append(f"[vplay_{i}]")

        # Freeze 1 — only if within segment_duration
        f1_start = curr + play_dur
        if f1_start < segment_duration:
            f1_dur = min(freeze1_dur, segment_duration - f1_start)
            if f1_z:
                filter_parts.append(
                    f"[0:v]trim=start={f1_start},select=eq(n\\,0),"
                    f"setpts=PTS-STARTPTS,{f1_z}[vf1_{i}];")
            else:
                filter_parts.append(
                    f"[0:v]trim=start={f1_start},select=eq(n\\,0),"
                    f"setpts=PTS-STARTPTS,loop=loop=-1:size=1:start=0,"
                    f"trim=duration={f1_dur}[vf1_{i}];")
            concat_inputs.append(f"[vf1_{i}]")

        # Freeze 2 — only if within segment_duration
        f2_start = curr + play_dur + freeze1_dur
        if f2_start < segment_duration:
            f2_dur = min(freeze2_dur, segment_duration - f2_start)
            if f2_z:
                filter_parts.append(
                    f"[0:v]trim=start={f2_start},select=eq(n\\,0),"
                    f"setpts=PTS-STARTPTS,{f2_z}[vf2_{i}];")
            else:
                filter_parts.append(
                    f"[0:v]trim=start={f2_start},select=eq(n\\,0),"
                    f"setpts=PTS-STARTPTS,loop=loop=-1:size=1:start=0,"
                    f"trim=duration={f2_dur}[vf2_{i}];")
            concat_inputs.append(f"[vf2_{i}]")

    # Concatenate video parts into a single video stream [v]
    filter_parts.append(
        f"{''.join(concat_inputs)}concat=n={len(concat_inputs)}:v=1:a=0[v]")

    return ''.join(filter_parts)


def edit_segment_with_retry(index, segment_path, segment_duration, output_dir,
                            play_dur, freeze1_dur, freeze2_dur,
                            freeze1_zoom, freeze2_zoom, zoom_dur,
                            max_retries=3):
    """Apply cycle repeat + zoom effects to a single speed-adjusted segment.
    Uses -shortest to prevent silent tails beyond segment duration."""
    for attempt in range(max_retries):
        try:
            output_path = os.path.join(output_dir, f"edited_{index}.mp4")
            filter_complex = build_cycle_filter(
                segment_path, segment_duration,
                play_dur, freeze1_dur, freeze2_dur,
                freeze1_zoom, freeze2_zoom, zoom_dur
            )

            # Apply video filter, keep original audio, use -shortest to trim silent tails
            cmd = ['ffmpeg', '-y', '-i', segment_path,
                   '-filter_complex', filter_complex,
                   '-map', '[v]', '-map', '0:a',
                   '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac',
                   '-shortest', output_path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True)

            if result.returncode == 0 and os.path.exists(output_path):
                if os.path.exists(segment_path):
                    os.remove(segment_path)
                return output_path
            else:
                raise Exception(f"FFmpeg failed: {result.stderr}")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                raise e


# ─────────────────────────────────────────────
# Merge all edited segments into final video
# ─────────────────────────────────────────────

def merge_videos(video_list, output_path):
    valid_videos = [v for v in video_list if v is not None and os.path.exists(v)]
    if not valid_videos:
        raise Exception("No valid segments to merge.")
    concat_file = "concat_list.txt"
    with open(concat_file, 'w') as f:
        for video in valid_videos:
            f.write(f"file '{os.path.abspath(video)}'\n")
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
           '-i', concat_file, '-c', 'copy', output_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    if os.path.exists(concat_file):
        os.remove(concat_file)
    if result.returncode != 0:
        raise Exception(f"Merge Error: {result.stderr}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    st.title("🎬 Video & Text Processor with TTS")

    with st.sidebar:
        st.header("⚙️ Settings")
        selected_voice = st.selectbox("Select Voice", options=[v["name"] for v in VOICES])
        voice_id = next(v["id"] for v in VOICES if v["name"] == selected_voice)
        col1, col2 = st.columns(2)
        with col1:
            selected_style = st.selectbox("Recap Style", options=[s["name"] for s in RECAP_STYLES])
            style_data = next(s for s in RECAP_STYLES if s["name"] == selected_style)
        with col2:
            selected_emotion = st.selectbox("Emotion", options=[e["name"] for e in EMOTIONS])
            emotion_data = next(e for e in EMOTIONS if e["name"] == selected_emotion)
        base_speed = style_data["speed"] + emotion_data["s"]
        base_pitch = style_data["pitch"] + emotion_data["p"]
        st.caption(f"📊 Base Speed: {base_speed}%, Base Pitch: {base_pitch}Hz")

        # Custom Speed slider with ±5 step buttons
        st.markdown("**🔊 Custom Speed Override**")
        col_sp1, col_sp2, col_sp3 = st.columns([1, 4, 1])
        with col_sp1:
            if st.button("➖", key="speed_down"):
                st.session_state.custom_speed = max(-100, st.session_state.get("custom_speed", 0) - 5)
        with col_sp2:
            custom_speed = st.slider("Speed (%)", -100, 100, st.session_state.get("custom_speed", 0), key="custom_speed_slider")
            st.session_state.custom_speed = custom_speed
        with col_sp3:
            if st.button("➕", key="speed_up"):
                st.session_state.custom_speed = min(100, st.session_state.get("custom_speed", 0) + 5)

        # Custom Pitch slider with ±5 step buttons
        st.markdown("**🎵 Custom Pitch Override**")
        col_pt1, col_pt2, col_pt3 = st.columns([1, 4, 1])
        with col_pt1:
            if st.button("➖", key="pitch_down"):
                st.session_state.custom_pitch = max(-100, st.session_state.get("custom_pitch", 0) - 5)
        with col_pt2:
            custom_pitch = st.slider("Pitch (Hz)", -100, 100, st.session_state.get("custom_pitch", 0), key="custom_pitch_slider")
            st.session_state.custom_pitch = custom_pitch
        with col_pt3:
            if st.button("➕", key="pitch_up"):
                st.session_state.custom_pitch = min(100, st.session_state.get("custom_pitch", 0) + 5)

        final_speed = base_speed + custom_speed
        final_pitch = base_pitch + custom_pitch
        st.caption(f"✅ Final Speed: {final_speed}%, Final Pitch: {final_pitch}Hz")

        st.markdown("---")
        play_duration = st.slider("▶️ Play Duration (s)", 1, 5, 3)
        col3, col4 = st.columns(2)
        with col3:
            freeze1_duration = st.slider("❄️ Freeze 1 (s)", 0, 2, 1)
            freeze1_zoom = st.selectbox("Zoom 1", ["None", "Zoom In", "Zoom Out"])
        with col4:
            freeze2_duration = st.slider("❄️ Freeze 2 (s)", 0, 2, 1)
            freeze2_zoom = st.selectbox("Zoom 2", ["None", "Zoom In", "Zoom Out"])
        zoom_duration = st.slider("🔍 Zoom Duration (s)", 0.1, 1.0, 0.5)
        st.markdown("---")
        text_input = st.text_area("📝 Enter Text", height=200)
        if text_input:
            paragraphs = count_paragraphs(text_input)
            st.info(f"📊 Paragraphs: {len(paragraphs)} | Characters: {len(text_input)}")
        video_file = st.file_uploader("🎥 Upload Video", type=["mp4", "mov", "avi"])

    if st.button("🚀 Start Processing"):
        if not text_input or not video_file:
            st.error("❌ Provide text and video.")
            return

        # Setup temp directories
        temp_dir = "temp_processing"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

        audio_dir = os.path.join(temp_dir, "audio")
        video_dir = os.path.join(temp_dir, "video")
        adjusted_dir = os.path.join(temp_dir, "adjusted")
        edited_dir = os.path.join(temp_dir, "edited")
        for d in [audio_dir, video_dir, adjusted_dir, edited_dir]:
            os.makedirs(d, exist_ok=True)

        video_path = os.path.join(video_dir, "input_video.mp4")

        # Chunk-by-chunk write to save RAM
        with open(video_path, "wb") as f:
            while chunk := video_file.read(8192):
                f.write(chunk)

        paragraphs = count_paragraphs(text_input)
        num_paragraphs = len(paragraphs)

        # ── Timer placeholders ──
        timer_placeholder = st.empty()
        progress_bar = st.progress(0)

        # Free RAM
        del video_file
        gc.collect()

        # Timer tracking
        total_start = time.time()

        # LiveTimer removed to prevent NoSessionContext errors.

        try:
            with st.status("🚀 Processing...", expanded=True) as status:

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # STEP 1/4: Pre-process Video + TTS + Split
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                progress_detail = st.empty()
                step_start = time.time()
                step_log = []

                # Pre-process video: cap at 900p, convert to 24fps
                orig_width, orig_height = get_video_resolution(video_path)
                needs_preprocess = (orig_width > 1600) or (orig_height > 900)

                if needs_preprocess:
                    optimized_video_path = os.path.join(video_dir, "optimized_900p_24fps.mp4")
                    progress_detail.markdown(f"⚙️ Video: {orig_width}×{orig_height} → Downscaling to 900p + 24fps...")
                    cmd = ['ffmpeg', '-y', '-i', video_path, '-vf', "scale='if(gt(iw,ih),1600,-2)':'if(gt(iw,ih),-2,1600)':force_original_aspect_ratio=decrease",
                           '-r', '24', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', optimized_video_path]
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    final_w, final_h = get_video_resolution(optimized_video_path)
                    video_opt_elapsed = time.time() - step_start
                    progress_detail.markdown(f"⚙️ Video: {orig_width}×{orig_height} → {final_w}×{final_h} @ 24fps ✓ ({video_opt_elapsed:.1f}s)")
                else:
                    optimized_video_path = os.path.join(video_dir, "optimized_24fps.mp4")
                    progress_detail.markdown(f"⚙️ Video: {orig_width}×{orig_height} → Converting to 24fps...")
                    cmd = ['ffmpeg', '-y', '-i', video_path, '-r', '24',
                           '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', optimized_video_path]
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    final_w, final_h = get_video_resolution(optimized_video_path)
                    video_opt_elapsed = time.time() - step_start
                    progress_detail.markdown(f"⚙️ Video: {orig_width}×{orig_height} → {final_w}×{final_h} @ 24fps ✓ ({video_opt_elapsed:.1f}s)")

                # Delete original high-res video immediately to save space/RAM
                if os.path.exists(video_path):
                    os.remove(video_path)
                video_path = optimized_video_path

                # Generate TTS in parallel with per-file progress
                progress_detail.markdown(f"🔊 Generating {num_paragraphs} TTS files in parallel...")
                tts_start = time.time()
                for i in range(num_paragraphs):
                    asyncio.run(generate_tts_async(
                        paragraphs[i],
                        os.path.join(audio_dir, f"audio_{i}.mp3"),
                        voice_id, final_speed, final_pitch
                    ))
                    progress_detail.markdown(f"🔊 TTS {i+1}/{num_paragraphs} complete")
                tts_elapsed = time.time() - tts_start
                progress_detail.markdown(f"🔊 TTS: {num_paragraphs}/{num_paragraphs} complete ({tts_elapsed:.1f}s)")

                # Split video
                progress_detail.markdown(f"✂️ Splitting video into {num_paragraphs} segments...")
                video_segments, seg_avg_dur = split_video(video_path, num_paragraphs, video_dir)
                for i in range(num_paragraphs):
                    progress_detail.markdown(f"✂️ Segment {i+1}/{num_paragraphs} split ✓")

                step1_elapsed = time.time() - step_start
                progress_bar.progress(0.15)
                step1_log = f"✅ Step 1/4: Pre-processing + TTS + Split — Complete ({step1_elapsed:.1f}s)"
                step_log.append(step1_log)
                progress_detail.markdown(step1_log)

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # STEP 2/4 + STEP 3/4: Speed-adjust → immediate Editing (PIPELINE)
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                step_start = time.time()
                edited_segments = [None] * num_paragraphs

                # Queue for passing speed-adjusted segments to the editor
                editing_queue = queue.Queue()
                speed_adjust_done = threading.Event()
                speed_adjust_errors = []

                def speed_adjust_worker(index, video_segment, audio_path, adjusted_dir, q):
                    """Worker: speed-adjust a segment then push to editing queue."""
                    try:
                        result = speed_adjust_segment(index, video_segment, audio_path, adjusted_dir)
                        adj_path, audio_dur, target_dur, speed_factor = result
                        q.put((index, adj_path, audio_dur, target_dur, speed_factor))
                    except Exception as e:
                        speed_adjust_errors.append((index, str(e)))
                        q.put((index, None, 0, 0, 0))  # Sentinel for error

                # Launch speed adjust workers (2 parallel)
                sa_threads = []
                for i in range(num_paragraphs):
                    t = threading.Thread(
                        target=speed_adjust_worker,
                        args=(i, video_segments[i],
                              os.path.join(audio_dir, f"audio_{i}.mp3"),
                              adjusted_dir, editing_queue)
                    )
                    sa_threads.append(t)
                    t.start()

                # Editing thread (1 sequential, RAM-safe)
                edit_done = threading.Event()
                edit_errors = []
                progress_detail.markdown(f"⚡ Speed-adjusting {num_paragraphs} segments (workers=2) + Editing (workers=1)...")

                def editing_worker():
                    """Worker: pull from queue and edit sequentially."""
                    completed_count = 0
                    while completed_count < num_paragraphs:
                        try:
                            item = editing_queue.get(timeout=600)
                        except queue.Empty:
                            break
                        idx, adj_path, audio_dur, target_dur, speed_factor = item
                        if adj_path is None:
                            completed_count += 1
                            editing_queue.task_done()
                            continue

                        # Show speed-adjust completion
                        sa_speed = f"{speed_factor:.2f}x" if speed_factor != 1.0 else "1.0x (unchanged)"
                        progress_detail.markdown(
                            f"⚡ Segment {idx+1}/{num_paragraphs}: speed-adjusted ✓ "
                            f"audio={audio_dur:.1f}s → target={target_dur:.1f}s ({sa_speed})"
                        )

                        # Edit immediately
                        edit_seg_start = time.time()
                        try:
                            cycle_duration = play_duration + freeze1_duration + freeze2_duration
                            num_cycles = math.ceil(target_dur / cycle_duration)
                            progress_detail.markdown(
                                f"🎬 Segment {idx+1}/{num_paragraphs}: editing (dur={target_dur:.1f}s, cycles={num_cycles})..."
                            )
                            edited_path = edit_segment_with_retry(
                                idx, adj_path, target_dur, edited_dir,
                                play_duration, freeze1_duration, freeze2_duration,
                                freeze1_zoom, freeze2_zoom, zoom_duration
                            )
                            edited_segments[idx] = edited_path
                            edit_elapsed = time.time() - edit_seg_start
                            progress_detail.markdown(
                                f"🎬 Segment {idx+1}/{num_paragraphs}: editing complete ✓ ({edit_elapsed:.1f}s)"
                            )
                        except Exception as e:
                            edit_errors.append((idx, str(e)))
                            st.error(f"❌ Segment {idx+1} editing failed: {e}")

                        completed_count += 1
                        # Update progress: 0.15 → 0.95 across speed+edit
                        progress_bar.progress(0.15 + 0.80 * completed_count / num_paragraphs)
                        editing_queue.task_done()

                    edit_done.set()

                # Start editing thread
                edit_thread = threading.Thread(target=editing_worker)
                edit_thread.start()

                # Wait for speed adjust workers to finish
                for t in sa_threads:
                    t.join()

                # Wait for editing thread to finish
                edit_thread.join()

                # Report speed adjust errors
                for idx, err in speed_adjust_errors:
                    st.error(f"❌ Speed adjust failed for segment {idx+1}: {err}")

                # Cleanup adjusted segments
                for seg in edited_segments:
                    if seg and os.path.exists(seg):
                        # adjusted segments are already removed by functions, but just in case
                        pass
                gc.collect()

                step23_elapsed = time.time() - step_start
                progress_bar.progress(0.95)
                step23_log = f"✅ Step 2/4 + Step 3/4: Speed-adjust + Edit {num_paragraphs} segments — Complete ({step23_elapsed:.1f}s)"
                step_log.append(step23_log)
                progress_detail.markdown(step23_log)

                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                # STEP 4/4: Merge all edited segments
                # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                step_start = time.time()
                progress_detail.markdown("🔗 Merging final video...")
                output_video = "final_output.mp4"
                try:
                    merge_videos(edited_segments, output_video)
                    progress_bar.progress(1.0)
                    merge_elapsed = time.time() - step_start
                    step4_log = f"✅ Step 4/4: Merge — Complete ({merge_elapsed:.1f}s)"
                    step_log.append(step4_log)
                    progress_detail.markdown(step4_log)
                    status.update(label="✅ Complete!", state="complete")
                except Exception as e:
                    st.error(f"❌ Final merge failed: {e}")
                    status.update(label="❌ Failed", state="error")
                    return

                # Show all persistent step completion indicators
                st.markdown("---")
                for log_entry in step_log:
                    st.markdown(log_entry)

        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            return

        # ── Final timer summary ──
        total_elapsed = time.time() - total_start
        timer_placeholder.markdown(f"⏱️ **Total: {format_time(total_elapsed)}**")
        st.success(f"🎉 Completed in **{format_time(total_elapsed)}**")

        # Download button
        if os.path.exists(output_video):
            st.download_button(
                "📥 Download Final Video",
                data=open(output_video, "rb"),
                file_name="output_video.mp4",
                mime="video/mp4"
            )

        # Final cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(output_video):
            os.remove(output_video)


if __name__ == "__main__":
    main()
