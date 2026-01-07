# 🎙️ AI Podcast Generation

Transform text content into engaging AI-generated podcast narrations with voice cloning capabilities.

## ✨ Features

- **📋 Text Input**: Paste any text content directly
- **🌐 Website Scraping**: Extract content from any URL using Firecrawl (optional)
- **🎭 Multiple Styles**: Choose from Conversational, Interview, Debate, or Educational narration formats
- **⏱️ Flexible Duration**: Generate podcasts from 5 to 20 minutes
- **🎵 Dual TTS Engines**: 
  - **Kokoro TTS**: Fast generation with default voice
  - **Chatterbox TTS**: Advanced voice cloning from reference audio
- **🎤 Voice Cloning**: Clone any voice by uploading a single 5-30 second audio sample
- **🎙️ Single-Speaker Narration**: Professional single-voice podcast format
- **📥 Export Options**: Download both scripts (JSON) and audio files (WAV)
- **📁 Local Storage**: All generated podcasts saved permanently to `podcast_outputs/`
- **🖥️ Device Support**: Automatic detection and optimization for CUDA, MPS (Apple Silicon), or CPU
- **🔑 Frontend API Keys**: Enter Groq and Firecrawl API keys directly in the UI

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or 3.12
- Groq API key (get from https://console.groq.com)
- Firecrawl API key (optional, for web scraping - get from https://firecrawl.dev)

### Installation

1. **Clone or navigate to the project:**
```bash
cd ai-podcast-generation
```

2. **Install dependencies:**
```bash
pip install -e .
```

3. **(Optional) Install Chatterbox for voice cloning:**
```bash
cd ../chatterbox
pip install -e .
cd ../ai-podcast-generation
```

### Running the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📖 Usage

### Step 1: Enter API Keys

In the sidebar settings:

1. **🤖 Groq API Key** (Required):
   - Enter your Groq API key
   - Get one from https://console.groq.com
   - Click "Save Groq Key"

2. **🔑 Firecrawl API Key** (Optional):
   - Only needed for web scraping
   - Get one from https://firecrawl.dev
   - Click "Save Firecrawl Key"

> **Note**: You can also set these in a `.env` file if preferred:
> ```
> GROQ_API_KEY=your_groq_key_here
> FIRECRAWL_API_KEY=your_firecrawl_key_here
> ```

### Step 2: Add Content

**Option A: Paste Text**
1. Go to "📋 Add Text" tab
2. Enter a source name
3. Paste your content
4. Click "Add Text Source"

**Option B: Scrape Website** (requires Firecrawl key)
1. In the sidebar, enter a URL
2. Click "Add Website"
3. Wait for content to be scraped

### Step 3: Generate Podcast

1. Navigate to the "🎙️ Studio" tab
2. Select your source from the dropdown
3. Choose podcast style:
   - **Conversational**: Natural, friendly narration
   - **Interview**: Narrative interview format
   - **Debate**: Exploring different perspectives
   - **Educational**: Clear explanatory narration
4. Choose duration (5, 10, 15, or 20 minutes)
5. **Select TTS Engine**:
   - **Kokoro (Fast)**: Quick generation with default voice
   - **Chatterbox (Voice Cloning)**: Clone custom voice
6. **(Optional) Upload Reference Audio** for voice cloning:
   - Upload one pre-recorded 5-30 second audio clip
   - This voice will be used for the podcast narration
   - Supports WAV, MP3, M4A formats
   - Use clear, high-quality recordings for best results
   - File upload only (no microphone recording)
7. Click "🎙️ Generate Podcast"
8. Wait for generation (5-15 minutes depending on length)
9. Download your podcast!

### Step 4: Access Your Files

Generated podcasts are saved to:
```
podcast_outputs/podcast_YYYYMMDD_HHMMSS/
├── segment_001_speaker.wav
├── segment_002_speaker.wav
├── segment_003_speaker.wav
├── ...
└── complete_podcast.wav  ← Main file to use!
```

## 🏗️ Project Structure

```
ai-podcast-generation/
├── app.py                          # Main Streamlit application
├── src/
│   ├── podcast/
│   │   ├── script_generator.py    # Podcast script generation (single-speaker)
│   │   └── text_to_speech.py      # Audio generation with TTS engines
│   └── web_scraping/
│       └── web_scraper.py          # Web content extraction
├── podcast_outputs/                # Generated podcasts (permanent storage)
├── pyproject.toml                  # Project dependencies
├── .env.example                    # Environment variables template (optional)
└── README.md                       # This file
```

## 🛠️ Technology Stack

- **Streamlit**: Web interface
- **Groq LLM**: Fast script generation via CrewAI
- **Kokoro TTS**: Fast text-to-speech synthesis
- **Chatterbox TTS**: Advanced voice cloning model
- **PyTorch**: Deep learning framework for voice cloning
- **Firecrawl**: Web content extraction (optional)

## 📝 Generated Output

The app generates:

1. **Podcast Script** (JSON format):
   - Single-speaker narration segments
   - Metadata including source, duration, and segment count
   - Downloadable JSON file

2. **Audio Files** (WAV format):
   - Individual segments for each narration part
   - Complete combined podcast with natural pauses
   - High-quality audio (22.05kHz for Chatterbox, 24kHz for Kokoro)

## 🔧 Configuration

### Podcast Settings

- **Style**: Conversational, Interview, Debate, Educational
- **Duration**: 5, 10, 15, or 20 minutes
- **TTS Engine**: Kokoro (fast) or Chatterbox (voice cloning)
- Configured in the Studio tab

### Audio Settings

**Kokoro TTS:**
- Default voice: `af_heart`
- Sample rate: 24000 Hz
- Pause duration: 0.2s between segments

**Chatterbox TTS:**
- Custom voice via reference audio
- Sample rate: 22050 Hz
- Pause duration: 0.5s between segments
- Automatic device detection (CUDA/MPS/CPU)
- Memory-efficient phase processing

## 🐛 Troubleshooting

### API Keys

**Groq API Key:**
- Enter in sidebar or set in `.env` file
- Get from https://console.groq.com
- Required for script generation

**Firecrawl API Key:**
- Optional - only needed for web scraping
- Get from https://firecrawl.dev
- Can use text input without this key

### TTS Not Available

**Kokoro TTS:**
```bash
pip install kokoro>=0.9.4
```

**Chatterbox TTS (Voice Cloning):**
```bash
# Install from the chatterbox directory
cd ../chatterbox
pip install -e .

# Or install dependencies manually
pip install torch torchaudio
```

### Memory Issues

If the app crashes during generation:

1. **Use shorter podcasts** (5 minutes instead of 10+)
2. **Close other applications** to free memory
3. **Use Kokoro TTS** for testing (much less memory)
4. **Restart app** between generations if needed

**Memory Requirements:**
- 5 min podcast: ~3 GB ✅ Safe
- 10 min podcast: ~4 GB ✅ Usually safe
- 15+ min podcast: ~5+ GB ⚠️ May crash on 8GB systems

### Files Not Saved

Generated files are saved to `podcast_outputs/` folder:

```bash
# List all generated podcasts
ls -la podcast_outputs/

# Play the latest podcast (macOS)
ls -t podcast_outputs/*/complete_podcast.wav | head -1 | xargs afplay

# Find all podcasts
find podcast_outputs/ -name "complete_podcast.wav"
```

### Import Errors

Make sure all dependencies are installed:
```bash
pip install -e .
```

## 💡 Workflow

```
1. Enter API Keys (Groq required)
   ↓
2. Add Content (Text or URL)
   ↓
3. Select source in Studio
   ↓
4. Configure style & duration
   ↓
5. Choose TTS engine
   ↓
6. (Optional) Upload reference audio
   ↓
7. Generate podcast
   ↓
8. Files saved to podcast_outputs/
   ↓
9. Download & enjoy!
```

## 🎯 Tips for Best Results

### Voice Cloning

**Good Reference Audio:**
- ✅ 15-30 seconds long
- ✅ Clear, single speaker
- ✅ Natural speech patterns
- ✅ Minimal background noise
- ✅ High quality (16kHz+)

**Avoid:**
- ❌ Multiple speakers
- ❌ Music or sound effects
- ❌ Very short clips (<5 seconds)
- ❌ Low quality recordings
- ❌ Heavy background noise

### Podcast Generation

1. **Start with short podcasts** (5 minutes) to test
2. **Use Kokoro** for quick iterations
3. **Use Chatterbox** for final voice-cloned version
4. **Close other apps** when using voice cloning
5. **Check `podcast_outputs/`** for saved files

## 📊 Performance

### Generation Times (10-minute podcast)

| Device | Kokoro | Chatterbox |
|--------|--------|------------|
| NVIDIA RTX 3090 | 1-2 min | 3-5 min |
| Apple M2 Max | 1-2 min | 5-8 min |
| Intel i7 (CPU) | 2-3 min | 15-25 min |

## 🆕 Recent Updates

- ✅ **Frontend API Keys**: Enter Groq and Firecrawl keys in UI
- ✅ **Single-Speaker Narration**: Professional single-voice format
- ✅ **Single Reference Audio**: One file for entire podcast
- ✅ **Local Storage**: Files saved to `podcast_outputs/`
- ✅ **Memory Management**: Improved stability and cleanup
- ✅ **JSON Script Display**: Clean script output format

