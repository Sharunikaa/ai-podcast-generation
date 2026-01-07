import logging
import os
import soundfile as sf
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import time
import re
import gc

try:
    from huggingface_hub import snapshot_download
except ImportError:  # pragma: no cover - optional optimisation dependency
    snapshot_download = None

try:
    import spacy
    from spacy.util import is_package
except ImportError:  # pragma: no cover - spaCy pulled in transitively by kokoro
    spacy = None
    is_package = None

try:
    from kokoro import KPipeline
except ImportError:
    print("Kokoro not installed. Install with: pip install kokoro>=0.9.4")
    KPipeline = None

try:
    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    CHATTERBOX_AVAILABLE = True
except ImportError:
    print("Chatterbox not installed. Voice cloning features will be disabled.")
    torch = None
    ta = None
    ChatterboxTTS = None
    CHATTERBOX_AVAILABLE = False

from src.podcast.script_generator import PodcastScript

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """Represents a single audio segment with metadata"""
    speaker: str
    text: str
    audio_data: Any
    duration: float
    file_path: str


class PodcastTTSGenerator:
    def __init__(self, lang_code: str = 'a', sample_rate: int = 24000):
        if KPipeline is None:
            raise ImportError("Kokoro TTS not available. Install with: pip install kokoro>=0.9.4 soundfile")

        self.sample_rate = sample_rate
        self._configure_cache_dirs()
        self._ensure_spacy_model()
        self._warm_kokoro_cache()

        self.pipeline = KPipeline(lang_code=lang_code, repo_id=os.getenv("KOKORO_REPO_ID", "hexgrad/Kokoro-82M"))

        # Single voice for all narration
        self.default_voice = "af_heart"  # Default voice

        logger.info(f"Kokoro TTS initialized with lang_code='{lang_code}', sample_rate={sample_rate}")

    def generate_podcast_audio(
        self,
        podcast_script: PodcastScript,
        output_dir: str = "outputs/podcast_audio",
        combine_audio: bool = True
    ) -> List[str]:

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating podcast audio for {podcast_script.total_lines} segments")
        logger.info(f"Output directory: {output_dir}")

        audio_segments = []
        output_files = []

        for i, line_dict in enumerate(podcast_script.script):
            speaker, dialogue = next(iter(line_dict.items()))

            logger.info(f"Processing segment {i+1}/{podcast_script.total_lines}: {speaker}")

            try:
                segment_audio = self._generate_single_segment(speaker, dialogue)
                segment_filename = f"segment_{i+1:03d}_{speaker.replace(' ', '_').lower()}.wav"
                segment_path = os.path.join(output_dir, segment_filename)

                sf.write(segment_path, segment_audio, self.sample_rate)
                output_files.append(segment_path)

                if combine_audio:
                    audio_segment = AudioSegment(
                        speaker=speaker,
                        text=dialogue,
                        audio_data=segment_audio,
                        duration=len(segment_audio) / self.sample_rate,
                        file_path=segment_path
                    )
                    audio_segments.append(audio_segment)

                logger.info(f"✓ Generated segment {i+1}: {segment_filename}")

            except Exception as e:
                logger.error(f"✗ Failed to generate segment {i+1}: {str(e)}")
                continue

        if combine_audio and audio_segments:
            combined_path = self._combine_audio_segments(audio_segments, output_dir)
            output_files.append(combined_path)

        logger.info(f"Podcast generation complete! Generated {len(output_files)} files")
        return output_files

    def _configure_cache_dirs(self) -> None:
        """Ensure consistent cache directories so large downloads persist between runs."""
        cache_root = Path(os.getenv("PODCAST_CACHE_DIR", Path.home() / ".podsite_cache"))
        cache_root.mkdir(parents=True, exist_ok=True)

        hf_cache = cache_root / "huggingface"
        kokoro_cache = cache_root / "kokoro"
        hf_cache.mkdir(parents=True, exist_ok=True)
        kokoro_cache.mkdir(parents=True, exist_ok=True)

        os.environ.setdefault("HF_HOME", str(hf_cache))
        os.environ.setdefault("KOKORO_HOME", str(kokoro_cache))
        os.environ.setdefault("KOKORO_REPO_ID", "hexgrad/Kokoro-82M")

    def _ensure_spacy_model(self) -> None:
        """Download spaCy's small English model once so Kokoro starts instantly."""
        if spacy is None or is_package is None:
            return

        model_name = "en_core_web_sm"
        if is_package(model_name):
            return

        try:
            from spacy.cli import download
            download(model_name)
        except Exception as exc:  # pragma: no cover - network/setup issues
            logger.warning("Unable to pre-download spaCy model %s: %s", model_name, exc)

    def _warm_kokoro_cache(self) -> None:
        """Prefetch Kokoro repository so the first utterance does not trigger downloads."""
        if snapshot_download is None:
            return

        repo_id = os.getenv("KOKORO_REPO_ID", "hexgrad/Kokoro-82M")
        try:
            snapshot_download(repo_id=repo_id, cache_dir=os.environ.get("HF_HOME"))
        except Exception as exc:  # pragma: no cover - best effort cache warmup
            logger.debug("Kokoro cache warmup skipped: %s", exc)

    def _generate_single_segment(self, speaker: str, text: str) -> Any:
        # Use default voice for all segments
        voice = self.default_voice
        clean_text = self._clean_text_for_tts(text)

        generator = self.pipeline(clean_text, voice=voice)

        combined_audio = []
        for i, (gs, ps, audio) in enumerate(generator):
            combined_audio.append(audio)

        if len(combined_audio) == 1:
            return combined_audio[0]
        else:
            import numpy as np
            return np.concatenate(combined_audio)

    def _clean_text_for_tts(self, text: str) -> str:
        clean_text = text.strip()

        clean_text = clean_text.replace("...", ".")
        clean_text = clean_text.replace("!!", "!")
        clean_text = clean_text.replace("??", "?")

        if not clean_text.endswith(('.', '!', '?')):
            clean_text += '.'

        return clean_text

    def _combine_audio_segments(
        self,
        segments: List[AudioSegment],
        output_dir: str
    ) -> str:
        logger.info(f"Combining {len(segments)} audio segments")

        try:
            import numpy as np

            pause_duration = 0.2  # seconds
            pause_samples = int(pause_duration * self.sample_rate)
            pause_audio = np.zeros(pause_samples, dtype=np.float32)

            combined_audio = []
            for i, segment in enumerate(segments):
                combined_audio.append(segment.audio_data)

                if i < len(segments) - 1:
                    combined_audio.append(pause_audio)

            final_audio = np.concatenate(combined_audio)

            combined_filename = "complete_podcast.wav"
            combined_path = os.path.join(output_dir, combined_filename)
            sf.write(combined_path, final_audio, self.sample_rate)

            duration = len(final_audio) / self.sample_rate
            logger.info(f"✓ Combined podcast saved: {combined_path} (Duration: {duration:.1f}s)")

            return combined_path

        except Exception as e:
            logger.error(f"✗ Failed to combine audio segments: {str(e)}")
            raise


class ChatterboxTTSGenerator:
    """
    Voice cloning TTS generator using Chatterbox model.
    Supports reference audio for voice cloning.
    """
    
    SAMPLE_RATE = 22050
    
    def __init__(self, device: Optional[str] = None):
        """
        Initialize Chatterbox TTS generator.
        
        Args:
            device: Device to use ('cuda', 'mps', 'cpu'). Auto-detects if None.
        """
        if not CHATTERBOX_AVAILABLE:
            raise ImportError(
                "Chatterbox TTS not available. Install required packages:\n"
                "pip install torch torchaudio"
            )
        
        # Enable MPS fallback for better compatibility
        os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
        
        self.device = device or self._detect_device()
        self._apply_device_fixes()
        
        logger.info(f"Loading Chatterbox TTS model on {self.device.upper()}...")
        try:
            self.model = ChatterboxTTS.from_pretrained(device=self.device)
            self.sr = self.model.sr
            logger.info(f"✅ Chatterbox TTS initialized successfully on {self.device.upper()}")
        except Exception as e:
            logger.error(f"Failed to load Chatterbox model on {self.device}: {e}")
            if self.device != "cpu":
                logger.info("Falling back to CPU...")
                self.device = "cpu"
                self.model = ChatterboxTTS.from_pretrained(device="cpu")
                self.sr = self.model.sr
                logger.info("✅ Chatterbox TTS initialized on CPU")
            else:
                raise
        finally:
            self._restore_torch_load()
        
        # Single reference audio for all speakers
        self.reference_audio_path = None
    
    def _detect_device(self) -> str:
        """Automatically detect the best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def _apply_device_fixes(self):
        """Apply device-specific compatibility fixes"""
        self.original_torch_load = torch.load
        
        def patched_torch_load(f, map_location=None, **kwargs):
            if map_location is None:
                map_location = self.device
            return self.original_torch_load(f, map_location=map_location, **kwargs)
        
        torch.load = patched_torch_load
        logger.info(f"✅ Device compatibility patch applied for {self.device.upper()}")
    
    def _restore_torch_load(self):
        """Restore original torch.load function"""
        if hasattr(self, 'original_torch_load'):
            torch.load = self.original_torch_load
    
    def set_reference_audio(self, audio_path: str):
        """
        Set reference audio for voice cloning (used for all speakers).
        
        Args:
            audio_path: Path to reference audio file
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")
        
        self.reference_audio_path = audio_path
        logger.info(f"✅ Reference audio set: {audio_path}")
    
    def _split_text_into_phases(self, text: str, max_chars_per_phase: int = 1000) -> List[str]:
        """Split text into manageable phases to avoid memory issues"""
        sentences = re.split(r'[.!?]+\s+', text)
        
        phases = []
        current_phase = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            
            if len(current_phase) + len(sentence) > max_chars_per_phase and current_phase:
                phases.append(current_phase.strip())
                current_phase = sentence
            else:
                current_phase += " " + sentence if current_phase else sentence
        
        if current_phase.strip():
            phases.append(current_phase.strip())
        
        # If we still have very long phases, split by words
        final_phases = []
        for phase in phases:
            if len(phase) > max_chars_per_phase * 1.5:
                words = phase.split()
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 > max_chars_per_phase and current_chunk:
                        final_phases.append(current_chunk.strip())
                        current_chunk = word
                    else:
                        current_chunk += " " + word if current_chunk else word
                
                if current_chunk.strip():
                    final_phases.append(current_chunk.strip())
            else:
                final_phases.append(phase)
        
        return final_phases
    
    def generate_podcast_audio(
        self,
        podcast_script: PodcastScript,
        output_dir: str = "outputs/podcast_audio",
        combine_audio: bool = True
    ) -> List[str]:
        """
        Generate podcast audio using Chatterbox TTS with optional voice cloning.
        
        Args:
            podcast_script: PodcastScript object containing the dialogue
            output_dir: Directory to save audio files
            combine_audio: Whether to combine segments into a complete podcast
        
        Returns:
            List of generated audio file paths
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating podcast audio for {podcast_script.total_lines} segments")
        logger.info(f"Output directory: {output_dir}")
        
        audio_segments = []
        output_files = []
        
        for i, line_dict in enumerate(podcast_script.script):
            speaker, dialogue = next(iter(line_dict.items()))
            
            logger.info(f"Processing segment {i+1}/{podcast_script.total_lines}: {speaker}")
            
            try:
                # Split long dialogue into phases
                phases = self._split_text_into_phases(dialogue, max_chars_per_phase=800)
                
                segment_audio_parts = []
                for phase_idx, phase in enumerate(phases):
                    logger.info(f"  Generating phase {phase_idx+1}/{len(phases)} ({len(phase)} chars)")
                    
                    # Use single reference audio if available
                    if self.reference_audio_path:
                        wav = self.model.generate(phase, audio_prompt_path=self.reference_audio_path)
                    else:
                        wav = self.model.generate(phase)
                    
                    segment_audio_parts.append(wav)
                    
                    # Clear memory after each phase
                    if hasattr(torch, 'cuda') and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        gc.collect()
                
                # Combine phases for this segment
                if len(segment_audio_parts) > 1:
                    # Add small pauses between phases
                    pause_duration = 0.3
                    pause_samples = int(self.sr * pause_duration)
                    pause_audio = torch.zeros(1, pause_samples)
                    
                    segment_audio = segment_audio_parts[0]
                    for part in segment_audio_parts[1:]:
                        segment_audio = torch.cat([segment_audio, pause_audio, part], dim=-1)
                else:
                    segment_audio = segment_audio_parts[0]
                
                # Convert to numpy for soundfile
                import numpy as np
                segment_audio_np = segment_audio.squeeze().cpu().numpy()
                
                segment_filename = f"segment_{i+1:03d}_{speaker.replace(' ', '_').lower()}.wav"
                segment_path = os.path.join(output_dir, segment_filename)
                
                sf.write(segment_path, segment_audio_np, self.sr)
                output_files.append(segment_path)
                
                if combine_audio:
                    audio_segment = AudioSegment(
                        speaker=speaker,
                        text=dialogue,
                        audio_data=segment_audio_np,
                        duration=len(segment_audio_np) / self.sr,
                        file_path=segment_path
                    )
                    audio_segments.append(audio_segment)
                
                logger.info(f"✓ Generated segment {i+1}: {segment_filename}")
                
            except Exception as e:
                logger.error(f"✗ Failed to generate segment {i+1}: {str(e)}")
                continue
        
        if combine_audio and audio_segments:
            combined_path = self._combine_audio_segments(audio_segments, output_dir)
            output_files.append(combined_path)
        
        logger.info(f"Podcast generation complete! Generated {len(output_files)} files")
        return output_files
    
    def _combine_audio_segments(
        self,
        segments: List[AudioSegment],
        output_dir: str
    ) -> str:
        """Combine audio segments into a complete podcast"""
        logger.info(f"Combining {len(segments)} audio segments")
        
        try:
            import numpy as np
            
            pause_duration = 0.5  # seconds
            pause_samples = int(pause_duration * self.sr)
            pause_audio = np.zeros(pause_samples, dtype=np.float32)
            
            combined_audio = []
            for i, segment in enumerate(segments):
                combined_audio.append(segment.audio_data)
                
                if i < len(segments) - 1:
                    combined_audio.append(pause_audio)
            
            final_audio = np.concatenate(combined_audio)
            
            combined_filename = "complete_podcast.wav"
            combined_path = os.path.join(output_dir, combined_filename)
            sf.write(combined_path, final_audio, self.sr)
            
            duration = len(final_audio) / self.sr
            logger.info(f"✓ Combined podcast saved: {combined_path} (Duration: {duration:.1f}s)")
            
            return combined_path
            
        except Exception as e:
            logger.error(f"✗ Failed to combine audio segments: {str(e)}")
            raise
