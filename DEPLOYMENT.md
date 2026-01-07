# 🚀 Deployment Guide

This guide covers deploying your AI Podcast Generation app to various cloud platforms.

## 📊 Platform Comparison

| Platform | RAM | Voice Cloning | Cost | Deployment Difficulty |
|----------|-----|---------------|------|---------------------|
| **Streamlit Community Cloud** | 1GB | ❌ Too low | Free | ⭐ Easiest |
| **Hugging Face Spaces** | 16GB | ✅ Perfect | Free | ⭐⭐ Easy |
| **Railway** | 8GB | ✅ Works | $5/mo | ⭐⭐ Easy |
| **Render** | 4GB+ | ✅ Works | $7/mo | ⭐⭐⭐ Medium |
| **Local** | Unlimited | ✅ Best | Free | ⭐ Easiest |

## 🎯 Recommended Deployment Strategy

### For Kokoro TTS Only (Fast, No Voice Cloning)
→ **Use Streamlit Community Cloud** (Free, Easy)

### For Chatterbox Voice Cloning
→ **Use Hugging Face Spaces** (Free, 16GB RAM, Perfect for AI models)

---

## 1️⃣ Streamlit Community Cloud (Kokoro Only)

**Best for:** Quick demos, text-to-speech without voice cloning

### Steps:

1. **Push to GitHub:**
```bash
git add .
git commit -m "Deploy to Streamlit Cloud"
git push origin main
```

2. **Deploy:**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Repository: `Sharunikaa/ai-podcast-generation`
   - Branch: `main`
   - Main file: `app.py`
   - Click "Deploy"

3. **Configure (Optional):**
   - Add secrets in app settings:
   ```toml
   GROQ_API_KEY = "your_key"
   FIRECRAWL_API_KEY = "your_key"
   ```

### ⚠️ Limitations:
- Only 1GB RAM (Chatterbox needs 2-4GB)
- Voice cloning will crash
- Use Kokoro TTS instead

---

## 2️⃣ Hugging Face Spaces (RECOMMENDED for Voice Cloning)

**Best for:** Full features including voice cloning, free 16GB RAM

### Steps:

1. **Create a Space:**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name: `ai-podcast-generation`
   - License: `mit`
   - SDK: `Streamlit`
   - Hardware: `CPU basic` (free, 16GB RAM)
   - Click "Create Space"

2. **Upload Files:**

**Option A: Via Git (Recommended)**
```bash
# Add HF remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ai-podcast-generation
git push hf main
```

**Option B: Via Web Interface**
- Upload all files from your project
- Make sure to include:
  - `app.py`
  - `requirements.txt`
  - `packages.txt`
  - `.streamlit/config.toml`
  - `src/` folder

3. **Configure:**
   - Go to Space settings → "Repository secrets"
   - Add secrets (optional):
   ```
   GROQ_API_KEY = your_key
   FIRECRAWL_API_KEY = your_key
   ```

4. **Wait for Build:**
   - HF will automatically install dependencies
   - First build takes 5-10 minutes
   - Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/ai-podcast-generation`

### ✅ Advantages:
- **16GB RAM** - Perfect for voice cloning!
- Free forever
- GPU upgrade available ($0.60/hour if needed)
- Great for AI/ML models
- Automatic builds

---

## 3️⃣ Railway (Voice Cloning Supported)

**Best for:** Production apps, 8GB RAM, good performance

### Steps:

1. **Sign up:** https://railway.app

2. **Deploy from GitHub:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `ai-podcast-generation`
   - Railway auto-detects Python

3. **Configure:**
   - Add environment variables:
   ```
   GROQ_API_KEY=your_key
   FIRECRAWL_API_KEY=your_key
   ```
   - Set start command: `streamlit run app.py --server.port=$PORT`

4. **Upgrade Plan:**
   - Free tier: 500 hours/month
   - Hobby plan: $5/month for 8GB RAM

### ✅ Advantages:
- 8GB RAM (voice cloning works!)
- Fast deployment
- Good for production
- Custom domains

---

## 4️⃣ Render (Voice Cloning Supported)

**Best for:** Professional deployments, scalable

### Steps:

1. **Sign up:** https://render.com

2. **Create Web Service:**
   - Click "New +"
   - Select "Web Service"
   - Connect GitHub repo
   - Name: `ai-podcast-generation`
   - Runtime: `Python 3`
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

3. **Configure:**
   - Instance type: Select 4GB+ RAM plan
   - Add environment variables:
   ```
   GROQ_API_KEY=your_key
   FIRECRAWL_API_KEY=your_key
   ```

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment

### ✅ Advantages:
- 4GB+ RAM available
- Professional hosting
- Auto-scaling
- Custom domains
- SSL included

---

## 5️⃣ Local Development (Best Performance)

**Best for:** Development, testing, maximum control

### Steps:

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the app:**
```bash
streamlit run app.py
```

3. **Access:**
   - Open http://localhost:8501

### ✅ Advantages:
- Unlimited RAM
- Fastest performance
- Full GPU access
- No deployment hassle
- Free

---

## 🔧 Deployment Checklist

Before deploying, ensure you have:

- [ ] `requirements.txt` with all dependencies
- [ ] `packages.txt` for system packages (HF Spaces)
- [ ] `.streamlit/config.toml` for UI settings
- [ ] `.gitignore` properly configured
- [ ] `README.md` with instructions
- [ ] API keys ready (Groq, Firecrawl)
- [ ] Tested locally first

---

## 🐛 Common Deployment Issues

### Issue: App crashes during voice cloning
**Solution:** Platform doesn't have enough RAM
- Use Hugging Face Spaces (16GB)
- Or use Kokoro TTS instead of Chatterbox

### Issue: Dependencies fail to install
**Solution:** Check `requirements.txt`
- Ensure all versions are compatible
- Pin versions if needed
- Check platform's Python version

### Issue: Models fail to download
**Solution:** Network/timeout issues
- Use platforms with good network (HF Spaces)
- Increase timeout settings
- Pre-download models if possible

### Issue: Audio files not saving
**Solution:** Filesystem permissions
- Check write permissions
- Use `/tmp` directory on some platforms
- Ensure `podcast_outputs/` exists

---

## 📊 Cost Comparison

| Platform | Free Tier | Paid Plan | Voice Cloning |
|----------|-----------|-----------|---------------|
| Streamlit Cloud | ✅ Unlimited | N/A | ❌ |
| HF Spaces | ✅ Unlimited | $0.60/hr GPU | ✅ |
| Railway | 500 hrs/mo | $5/mo | ✅ |
| Render | 750 hrs/mo | $7/mo | ✅ |
| Local | ✅ Free | N/A | ✅ |

---

## 🎯 Final Recommendation

**For Most Users:**
1. **Start with Streamlit Cloud** (test Kokoro TTS)
2. **Upgrade to HF Spaces** (when you need voice cloning)
3. **Go local** (for development and best performance)

**For Production:**
- **Hugging Face Spaces** (free, reliable, 16GB RAM)
- **Railway** (paid, professional, scalable)

---

## 📚 Additional Resources

- [Streamlit Deployment Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [HF Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)

---

## 💡 Pro Tips

1. **Test locally first** before deploying
2. **Use environment variables** for API keys
3. **Monitor memory usage** in production
4. **Start with free tiers** before upgrading
5. **Use Kokoro for demos**, Chatterbox for production
6. **Keep dependencies minimal** for faster builds
7. **Enable error logging** for debugging

---

**Need help?** Open an issue on GitHub!

