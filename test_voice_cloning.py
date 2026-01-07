#!/usr/bin/env python3
"""
Test script for Chatterbox voice cloning integration
"""
import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
    except ImportError as e:
        print(f"❌ PyTorch not available: {e}")
        return False
    
    try:
        import torchaudio
        print(f"✅ TorchAudio {torchaudio.__version__}")
    except ImportError as e:
        print(f"❌ TorchAudio not available: {e}")
        return False
    
    # SoundDevice is no longer required (removed recording feature)
    print("ℹ️  SoundDevice not required (file upload only)")
    
    try:
        from chatterbox.tts import ChatterboxTTS
        print("✅ Chatterbox TTS")
    except ImportError as e:
        print(f"❌ Chatterbox TTS not available: {e}")
        print("   Install with: cd ../chatterbox && pip install -e .")
        return False
    
    try:
        from src.podcast.text_to_speech import ChatterboxTTSGenerator, CHATTERBOX_AVAILABLE
        print(f"✅ ChatterboxTTSGenerator (Available: {CHATTERBOX_AVAILABLE})")
    except ImportError as e:
        print(f"❌ ChatterboxTTSGenerator not available: {e}")
        return False
    
    return True


def test_device_detection():
    """Test device detection"""
    print("\n🖥️ Testing device detection...")
    
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
            device = "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("✅ MPS (Apple Silicon) available")
            device = "mps"
        else:
            print("✅ Using CPU")
            device = "cpu"
        
        print(f"   Selected device: {device}")
        return True, device
        
    except Exception as e:
        print(f"❌ Device detection failed: {e}")
        return False, None


def test_generator_initialization(device):
    """Test ChatterboxTTSGenerator initialization"""
    print("\n🎤 Testing ChatterboxTTSGenerator initialization...")
    
    try:
        from src.podcast.text_to_speech import ChatterboxTTSGenerator
        
        print(f"   Initializing on {device}...")
        generator = ChatterboxTTSGenerator(device=device)
        print(f"✅ Generator initialized successfully")
        print(f"   Sample rate: {generator.sr} Hz")
        print(f"   Device: {generator.device}")
        
        return True, generator
        
    except Exception as e:
        print(f"❌ Generator initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_basic_generation(generator):
    """Test basic text-to-speech generation"""
    print("\n🎵 Testing basic audio generation...")
    
    try:
        from src.podcast.script_generator import PodcastScript
        
        # Create a simple test script
        test_script = PodcastScript(
            script=[
                {"Speaker 1": "Hello! Welcome to our test podcast."},
                {"Speaker 2": "Thanks for having me! This is a test of the voice cloning system."}
            ],
            source_document="Test",
            total_lines=2,
            estimated_duration="30 seconds"
        )
        
        print("   Generating audio for test script...")
        output_dir = "test_output"
        Path(output_dir).mkdir(exist_ok=True)
        
        audio_files = generator.generate_podcast_audio(
            podcast_script=test_script,
            output_dir=output_dir,
            combine_audio=True
        )
        
        print(f"✅ Generated {len(audio_files)} audio files")
        for file in audio_files:
            size = os.path.getsize(file) / 1024  # KB
            print(f"   - {file} ({size:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reference_audio_setting(generator):
    """Test setting reference audio"""
    print("\n🎭 Testing reference audio setting...")
    
    try:
        # Test with a non-existent file (should fail gracefully)
        try:
            generator.set_reference_audio("Speaker 1", "nonexistent.wav")
            print("⚠️ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError:
            print("✅ Correctly handles missing reference audio")
        
        # Test with invalid speaker
        try:
            generator.set_reference_audio("Invalid Speaker", "test.wav")
            print("⚠️ Should have raised ValueError")
            return False
        except ValueError:
            print("✅ Correctly validates speaker names")
        
        return True
        
    except Exception as e:
        print(f"❌ Reference audio test failed: {e}")
        return False


def cleanup():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    import shutil
    test_dir = "test_output"
    
    if os.path.exists(test_dir):
        try:
            shutil.rmtree(test_dir)
            print(f"✅ Removed {test_dir}")
        except Exception as e:
            print(f"⚠️ Could not remove {test_dir}: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("🎙️ Chatterbox Voice Cloning Integration Test")
    print("=" * 60)
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Import test failed. Please install missing dependencies.")
        return False
    
    # Test 2: Device detection
    success, device = test_device_detection()
    if not success:
        print("\n❌ Device detection failed.")
        return False
    
    # Test 3: Generator initialization
    success, generator = test_generator_initialization(device)
    if not success:
        print("\n❌ Generator initialization failed.")
        return False
    
    # Test 4: Reference audio setting
    if not test_reference_audio_setting(generator):
        print("\n❌ Reference audio test failed.")
        return False
    
    # Test 5: Basic generation
    if not test_basic_generation(generator):
        print("\n❌ Audio generation test failed.")
        return False
    
    # Cleanup
    cleanup()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\n📖 Next steps:")
    print("   1. Run the Streamlit app: streamlit run app.py")
    print("   2. Select 'Chatterbox (Voice Cloning)' as TTS engine")
    print("   3. Upload reference audio for voice cloning")
    print("   4. Generate your podcast!")
    print("\n📚 For more information, see VOICE_CLONING_GUIDE.md")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)

