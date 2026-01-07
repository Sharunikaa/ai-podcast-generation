#!/usr/bin/env python3
"""
Simple integration test for Chatterbox voice cloning
Tests imports and structure without loading models
"""
import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    errors = []
    
    # Test PyTorch
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
    except ImportError as e:
        errors.append(f"PyTorch: {e}")
        print(f"❌ PyTorch not available")
    
    # Test TorchAudio
    try:
        import torchaudio
        print(f"✅ TorchAudio {torchaudio.__version__}")
    except ImportError as e:
        errors.append(f"TorchAudio: {e}")
        print(f"❌ TorchAudio not available")
    
    # SoundDevice is no longer required (removed recording feature)
    # Only file upload is supported
    
    # Test Chatterbox
    try:
        from chatterbox.tts import ChatterboxTTS
        print("✅ Chatterbox TTS")
    except ImportError as e:
        errors.append(f"Chatterbox: {e}")
        print(f"❌ Chatterbox TTS not available")
        print("   Install with: cd ../chatterbox && pip install -e .")
    
    # Test our integration
    try:
        from src.podcast.text_to_speech import (
            ChatterboxTTSGenerator, 
            CHATTERBOX_AVAILABLE,
            PodcastTTSGenerator
        )
        print(f"✅ ChatterboxTTSGenerator (Available: {CHATTERBOX_AVAILABLE})")
        print(f"✅ PodcastTTSGenerator (Kokoro)")
    except ImportError as e:
        errors.append(f"Integration: {e}")
        print(f"❌ Integration modules not available")
    
    return len(errors) == 0, errors


def test_structure():
    """Test class structure and methods"""
    print("\n🏗️ Testing class structure...")
    
    try:
        from src.podcast.text_to_speech import ChatterboxTTSGenerator
        
        # Check if class has required methods
        required_methods = [
            'generate_podcast_audio',
            'set_reference_audio',
            '_detect_device',
            '_split_text_into_phases',
            '_combine_audio_segments'
        ]
        
        for method in required_methods:
            if hasattr(ChatterboxTTSGenerator, method):
                print(f"✅ Method: {method}")
            else:
                print(f"❌ Missing method: {method}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False


def test_app_integration():
    """Test app.py integration"""
    print("\n📱 Testing app.py integration...")
    
    try:
        # Check if app.py imports correctly
        import app
        
        # Check session state initialization
        if hasattr(app, 'init_session_state'):
            print("✅ init_session_state function exists")
        else:
            print("❌ init_session_state function missing")
            return False
        
        # Check if generate_podcast has tts_engine parameter
        import inspect
        sig = inspect.signature(app.generate_podcast)
        params = list(sig.parameters.keys())
        
        if 'tts_engine' in params:
            print("✅ generate_podcast has tts_engine parameter")
        else:
            print("❌ generate_podcast missing tts_engine parameter")
            return False
        
        print("✅ App integration looks good")
        return True
        
    except Exception as e:
        print(f"❌ App integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_dependencies():
    """Check pyproject.toml dependencies"""
    print("\n📦 Checking dependencies...")
    
    try:
        import tomli
    except ImportError:
        # Try tomllib (Python 3.11+)
        try:
            import tomllib as tomli
        except ImportError:
            print("⚠️ Cannot check dependencies (tomli/tomllib not available)")
            return True
    
    try:
        with open('pyproject.toml', 'rb') as f:
            data = tomli.load(f)
        
        deps = data.get('project', {}).get('dependencies', [])
        
        required = ['torch', 'torchaudio']
        for req in required:
            found = any(req in dep for dep in deps)
            if found:
                print(f"✅ {req} in dependencies")
            else:
                print(f"⚠️ {req} not in dependencies")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Could not check dependencies: {e}")
        return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("🎙️ Chatterbox Voice Cloning Integration Test")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Imports
    success, errors = test_imports()
    if not success:
        print("\n⚠️ Some imports failed:")
        for error in errors:
            print(f"   - {error}")
        all_passed = False
    
    # Test 2: Structure
    if not test_structure():
        print("\n❌ Structure test failed")
        all_passed = False
    
    # Test 3: App integration
    if not test_app_integration():
        print("\n❌ App integration test failed")
        all_passed = False
    
    # Test 4: Dependencies
    check_dependencies()
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ Integration tests passed!")
        print("=" * 60)
        print("\n📖 Next steps:")
        print("   1. Install dependencies: pip install -e .")
        print("   2. Install Chatterbox: cd ../chatterbox && pip install -e .")
        print("   3. Run the app: streamlit run app.py")
        print("   4. Select 'Chatterbox (Voice Cloning)' as TTS engine")
        print("\n📚 For more information, see VOICE_CLONING_GUIDE.md")
    else:
        print("⚠️ Some tests failed - see details above")
        print("=" * 60)
        print("\n🔧 Troubleshooting:")
        print("   - Install missing dependencies")
        print("   - Check that Chatterbox is installed")
        print("   - See VOICE_CLONING_GUIDE.md for help")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

