import streamlit as st
import os
import tempfile
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.podcast.script_generator import PodcastScriptGenerator
from src.podcast.text_to_speech import PodcastTTSGenerator, ChatterboxTTSGenerator, CHATTERBOX_AVAILABLE
from src.web_scraping.web_scraper import WebScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Podsite - AI Podcast Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 24px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 20px;
    }

    .source-item {
        background: #2d3748;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 3px solid #4299e1;
    }

    .source-title {
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
    }

    .source-meta {
        font-size: 12px;
        color: #a0aec0;
    }

    .script-segment {
        background: #1a202c;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
    }

    .speaker-1 {
        border-left: 3px solid #ec4899;
    }

    .speaker-2 {
        border-left: 3px solid #10b981;
    }

    .stButton > button {
        background: #4299e1;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 24px;
        font-weight: 500;
    }

    .source-count {
        background: #4a5568;
        color: #ffffff;
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    if 'sources' not in st.session_state:
        st.session_state.sources = []
    if 'script_generator' not in st.session_state:
        st.session_state.script_generator = None
    if 'tts_generator' not in st.session_state:
        st.session_state.tts_generator = None
    if 'chatterbox_tts_generator' not in st.session_state:
        st.session_state.chatterbox_tts_generator = None
    if 'web_scraper' not in st.session_state:
        st.session_state.web_scraper = None
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'groq_key' not in st.session_state:
        st.session_state.groq_key = os.getenv("GROQ_API_KEY", "")
    if 'firecrawl_key' not in st.session_state:
        st.session_state.firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")
    if 'tts_engine' not in st.session_state:
        st.session_state.tts_engine = "kokoro"  # Default to Kokoro
    if 'reference_audio' not in st.session_state:
        st.session_state.reference_audio = None

def initialize_generators():
    if st.session_state.initialized:
        return True

    if not st.session_state.groq_key:
        return False

    try:
        st.session_state.script_generator = PodcastScriptGenerator(st.session_state.groq_key)

        # Initialize Kokoro TTS in background - don't block UI
        if st.session_state.tts_generator is None:
            try:
                st.session_state.tts_generator = PodcastTTSGenerator()
                logger.info("Kokoro TTS Generator initialized successfully")
            except ImportError:
                logger.warning("Kokoro TTS not available.")
                st.session_state.tts_generator = None
            except Exception as e:
                logger.error(f"Error initializing Kokoro TTS: {e}")
                st.session_state.tts_generator = None

        # Initialize Chatterbox TTS if available
        if st.session_state.chatterbox_tts_generator is None and CHATTERBOX_AVAILABLE:
            try:
                st.session_state.chatterbox_tts_generator = ChatterboxTTSGenerator()
                logger.info("Chatterbox TTS Generator initialized successfully")
            except ImportError:
                logger.warning("Chatterbox TTS not available. Voice cloning features will be disabled.")
                st.session_state.chatterbox_tts_generator = None
            except Exception as e:
                logger.error(f"Error initializing Chatterbox TTS: {e}")
                st.session_state.chatterbox_tts_generator = None

        st.session_state.initialized = True
        return True

    except Exception as e:
        st.error(f"❌ Failed to initialize: {str(e)}")
        logger.error(f"Initialization error: {e}")
        return False

def initialize_web_scraper(api_key: str):
    """Initialize or reinitialize web scraper with provided API key"""
    if api_key:
        try:
            st.session_state.web_scraper = WebScraper(api_key)
            st.session_state.firecrawl_key = api_key
            logger.info("Web scraper initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize web scraper: {e}")
            st.error(f"❌ Failed to initialize web scraper: {str(e)}")
            return False
    return False

def add_url_source(url: str):
    if not st.session_state.web_scraper:
        st.error("Web scraper not available. Please add FIRECRAWL_API_KEY to your .env file.")
        return

    with st.spinner(f"Scraping {url}..."):
        try:
            result = st.session_state.web_scraper.scrape_url(url)

            if result['success'] and result['content']:
                source_info = {
                    'name': result['title'],
                    'url': url,
                    'type': 'Website',
                    'content': result['content'],
                    'word_count': result['word_count'],
                    'added_at': time.strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.sources.append(source_info)
                st.success(f"✅ Added: {result['title']} ({result['word_count']} words)")
            else:
                st.error(f"❌ Failed to scrape URL: {result.get('error', 'No content found')}")

        except Exception as e:
            st.error(f"❌ Error scraping URL: {str(e)}")
            logger.error(f"URL scraping error: {e}")

def add_text_source(text_content: str, source_name: str):
    if not text_content.strip():
        st.warning("Please enter some text content")
        return

    source_info = {
        'name': source_name,
        'url': None,
        'type': 'Text',
        'content': text_content,
        'word_count': len(text_content.split()),
        'added_at': time.strftime("%Y-%m-%d %H:%M")
    }
    st.session_state.sources.append(source_info)
    st.success(f"✅ Added: {source_name} ({len(text_content.split())} words)")

def remove_source(index: int):
    if 0 <= index < len(st.session_state.sources):
        removed = st.session_state.sources.pop(index)
        st.success(f"✅ Removed: {removed['name']}")
        st.rerun()

def render_sources_sidebar():
    with st.sidebar:
        st.markdown('<div class="main-header">⚙️ Settings</div>', unsafe_allow_html=True)

        # Groq API Key input
        st.markdown("#### 🤖 Groq API Key")
        groq_input = st.text_input(
            "Enter Groq API Key",
            value=st.session_state.groq_key if st.session_state.groq_key else "",
            type="password",
            help="Required for script generation. Get your key from https://console.groq.com",
            key="groq_input"
        )

        if groq_input != st.session_state.groq_key:
            if st.button("Save Groq Key", use_container_width=True, key="save_groq"):
                st.session_state.groq_key = groq_input
                st.session_state.initialized = False  # Force reinitialization
                if initialize_generators():
                    st.success("✅ Groq API key saved!")
                    st.rerun()
                else:
                    st.error("❌ Failed to initialize with this key")

        st.markdown("---")

        # Firecrawl API Key input
        st.markdown("#### 🔑 Firecrawl API Key")
        firecrawl_input = st.text_input(
            "Enter Firecrawl API Key",
            value=st.session_state.firecrawl_key if st.session_state.firecrawl_key else "",
            type="password",
            help="Optional: For web scraping. Get your key from https://firecrawl.dev",
            key="firecrawl_input"
        )

        if firecrawl_input != st.session_state.firecrawl_key:
            if st.button("Save Firecrawl Key", use_container_width=True, key="save_firecrawl"):
                if initialize_web_scraper(firecrawl_input):
                    st.success("✅ Firecrawl API key saved!")
                    st.rerun()

        st.markdown("---")

        # Add URL section
        st.markdown("#### 🌐 Add Website")
        url_input = st.text_input(
            "Website URL",
            placeholder="https://example.com/article",
            help="Paste a URL to scrape content",
            key="sidebar_url"
        )

        if st.button("Add Website", key="sidebar_add_url", use_container_width=True):
            if url_input.strip():
                add_url_source(url_input.strip())
                st.rerun()
            else:
                st.warning("Please enter a URL")

        st.markdown("---")

        # Sources list
        st.markdown('<div class="main-header">📚 Sources</div>', unsafe_allow_html=True)

        if st.session_state.sources:
            st.markdown(f'<div class="source-count">{len(st.session_state.sources)} sources</div>', unsafe_allow_html=True)

            for i, source in enumerate(st.session_state.sources):
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f'''
                        <div class="source-item">
                            <div class="source-title">{source['name']}</div>
                            <div class="source-meta">{source['type']} • {source['word_count']} words</div>
                            <div class="source-meta">{source['added_at']}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    with col2:
                        if st.button("🗑️", key=f"del_{i}", help="Remove source"):
                            remove_source(i)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 20px; color: #a0aec0;">
                <p>No sources added yet</p>
                <p style="font-size: 14px;">Add websites or text to generate podcasts</p>
            </div>
            """, unsafe_allow_html=True)

def generate_podcast(selected_source_name: str, podcast_style: str, podcast_length: str, tts_engine: str):
    # Check if Groq API key is set
    if not st.session_state.groq_key:
        st.error("❌ Please enter your Groq API key in the sidebar settings")
        return
    
    if not st.session_state.script_generator:
        st.error("❌ Script generator not initialized. Please check your Groq API key.")
        return

    source_info = None
    for source in st.session_state.sources:
        if source['name'] == selected_source_name:
            source_info = source
            break

    if not source_info:
        st.error("Source not found")
        return

    try:
        with st.spinner("✍️ Generating podcast script..."):
            podcast_script = st.session_state.script_generator.generate_script_from_text(
                text_content=source_info['content'],
                source_name=source_info['name'],
                podcast_style=podcast_style.lower(),
                target_duration=podcast_length
            )

        # Select TTS generator based on engine choice
        tts_gen = None
        if tts_engine == "chatterbox" and st.session_state.chatterbox_tts_generator:
            tts_gen = st.session_state.chatterbox_tts_generator
            engine_name = "Chatterbox (Voice Cloning)"
        elif tts_engine == "kokoro" and st.session_state.tts_generator:
            tts_gen = st.session_state.tts_generator
            engine_name = "Kokoro"
        
        if tts_gen:
            with st.spinner(f"🎵 Generating podcast audio with {engine_name}... This may take several minutes..."):
                try:
                    # Create permanent output directory
                    output_base = Path("podcast_outputs")
                    output_base.mkdir(exist_ok=True)
                    
                    timestamp = time.strftime('%Y%m%d_%H%M%S')
                    output_dir = output_base / f"podcast_{timestamp}"
                    output_dir.mkdir(exist_ok=True)

                    # Set reference audio for Chatterbox if available
                    if tts_engine == "chatterbox" and st.session_state.reference_audio:
                        tts_gen.set_reference_audio(st.session_state.reference_audio)

                    audio_files = tts_gen.generate_podcast_audio(
                        podcast_script=podcast_script,
                        output_dir=str(output_dir),
                        combine_audio=True
                    )

                    st.info(f"📁 Files saved to: {output_dir}")

                    st.markdown("### 🎙️ Generated Podcast")
                    for audio_file in audio_files:
                        file_name = Path(audio_file).name

                        if "complete_podcast" in file_name:
                            st.audio(audio_file, format="audio/wav")

                            with open(audio_file, "rb") as f:
                                st.download_button(
                                    label="📥 Download Complete Podcast",
                                    data=f.read(),
                                    file_name=f"podcast_{timestamp}.wav",
                                    mime="audio/wav"
                                )

                except Exception as e:
                    st.error(f"❌ Audio generation failed: {str(e)}")
                    logger.error(f"Audio generation error: {e}")
                finally:
                    # Aggressive memory cleanup to prevent app crash
                    import gc
                    
                    if tts_engine == "chatterbox":
                        try:
                            import torch
                            
                            # Unload the model from memory
                            if hasattr(tts_gen, 'model'):
                                del tts_gen.model
                                logger.info("🗑️ Unloaded Chatterbox model")
                            
                            # Clear GPU cache
                            if hasattr(torch, 'cuda') and torch.cuda.is_available():
                                torch.cuda.empty_cache()
                                torch.cuda.synchronize()
                            
                            # Clear MPS cache (Apple Silicon)
                            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                                torch.mps.empty_cache()
                                torch.mps.synchronize()
                            
                            # Force garbage collection multiple times
                            for _ in range(3):
                                gc.collect()
                            
                            # Reinitialize the model for next use
                            try:
                                st.session_state.chatterbox_tts_generator = None
                                from src.podcast.text_to_speech import ChatterboxTTSGenerator
                                st.session_state.chatterbox_tts_generator = ChatterboxTTSGenerator()
                                logger.info("♻️ Reinitialized Chatterbox model")
                            except Exception as reinit_error:
                                logger.warning(f"Could not reinitialize model: {reinit_error}")
                            
                            logger.info("✅ Memory cleaned up successfully")
                        except Exception as e:
                            logger.warning(f"Memory cleanup warning: {e}")
                    
                    # Final garbage collection
                    gc.collect()
        else:
            st.warning(f"⚠️ {engine_name} TTS not available. Please check installation.")

        st.markdown("### 📝 Generated Podcast Script")

        # Display script as JSON
        script_json = podcast_script.to_json()
        st.json(script_json)
        
        st.download_button(
            label="📥 Download Script (JSON)",
            data=script_json,
            file_name=f"podcast_script_{int(time.time())}.json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"❌ Podcast generation failed: {str(e)}")
        logger.error(f"Podcast generation error: {e}")

def render_add_sources_tab():
    st.markdown("### 📁 Add Text Source")
    st.markdown("""
    Paste text content to create podcasts. Use the sidebar to add website URLs.
    """)

    source_name = st.text_input(
        "Source Name",
        placeholder="e.g., Article Title, Research Notes",
        help="Give your text content a name"
    )

    text_content = st.text_area(
        "Text Content",
        placeholder="Paste your text here...",
        height=400,
        help="Enter the text content you want to convert into a podcast"
    )

    if st.button("Add Text Source", use_container_width=True) and text_content.strip():
        name = source_name.strip() if source_name.strip() else f"Text ({time.strftime('%H:%M')})"
        add_text_source(text_content, name)
        st.rerun()

def render_studio_tab():
    

    if not st.session_state.sources:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #a0aec0;">
            <p>No sources available</p>
            <p>Add sources in the "Add Sources" tab to generate podcasts!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("#### 🎙️ Generate Podcast")
        st.markdown("Create an AI-generated podcast discussion from your content")

        source_names = [source['name'] for source in st.session_state.sources]
        selected_source = st.selectbox(
            "Select Source",
            source_names,
            help="Choose content to create a podcast from"
        )

        col1, col2 = st.columns(2)
        with col1:
            podcast_style = st.selectbox(
                "Podcast Style",
                ["Conversational", "Interview", "Debate", "Educational"]
            )
        with col2:
            podcast_length = st.selectbox(
                "Duration",
                ["5 minutes", "10 minutes", "15 minutes", "20 minutes"],
                index=1
            )

        # TTS Engine Selection
        st.markdown("---")
        st.markdown("#### 🎤 Voice Settings")
        
        tts_options = []
        if st.session_state.tts_generator:
            tts_options.append("Kokoro (Fast)")
        if st.session_state.chatterbox_tts_generator:
            tts_options.append("Chatterbox (Voice Cloning)")
        
        if not tts_options:
            st.warning("⚠️ No TTS engines available. Please check installation.")
            return
        
        tts_engine_display = st.selectbox(
            "TTS Engine",
            tts_options,
            help="Choose the text-to-speech engine"
        )
        
        # Map display name to internal name
        tts_engine = "kokoro" if "Kokoro" in tts_engine_display else "chatterbox"
        
        # Voice Cloning Options (only for Chatterbox)
        if tts_engine == "chatterbox":
            st.markdown("##### 🎭 Voice Cloning (Optional)")
            st.markdown("Upload one reference audio file to clone the voice for the podcast narration")

            reference_file = st.file_uploader(
                "Upload Reference Audio",
                type=["wav", "mp3", "m4a"],
                key="reference_upload",
                help="Upload a 5-30 second audio clip of the voice you want to clone for the narration"
            )
            
            if reference_file:
                # Save uploaded file
                temp_path = os.path.join(tempfile.gettempdir(), f"reference_audio_{int(time.time())}.wav")
                with open(temp_path, "wb") as f:
                    f.write(reference_file.read())
                st.session_state.reference_audio = temp_path
                st.success("✅ Reference audio uploaded")
                st.audio(temp_path)
            elif st.session_state.reference_audio:
                st.info("✓ Reference audio set")
                if st.button("Clear Reference Audio", key="clear_reference"):
                    st.session_state.reference_audio = None
                    st.rerun()

        st.markdown("---")
        if st.button("🎙️ Generate Podcast", use_container_width=True):
            if selected_source:
                generate_podcast(selected_source, podcast_style, podcast_length, tts_engine)
            else:
                st.warning("Please select a source")

def main():
    init_session_state()

    st.markdown("""
    <div style="text-align: center;">
        <h1 style="color: #ffffff; margin: 0;">🎙️ Podsite</h1>
        <p style="color: #a0aec0; font-size: 18px;">Transform Web Content into Engaging Podcasts</p>
    </div>
    """, unsafe_allow_html=True)

    initialize_generators()

    render_sources_sidebar()

    tab1, tab2 = st.tabs(["📋 Add Text", "🎙️ Studio"])

    with tab1:
        render_add_sources_tab()

    with tab2:
        render_studio_tab()

    

if __name__ == "__main__":
    main()
