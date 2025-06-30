# 🏠 Local LLM Setup with LM Studio

Run JobSite completely privately with local AI models - no API keys, no data sharing, no costs!

## 📥 **Step 1: Install LM Studio**

1. **Download LM Studio**: https://lmstudio.ai/
2. **Install** the application (available for Mac, Windows, Linux)
3. **Launch** LM Studio

## 🤖 **Step 2: Download Recommended Models**

For job scraping, these models offer the best balance of speed, accuracy, and size:

### 🥇 **Top Choice: Llama 3.1 8B Instruct**
- **Model**: `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF`
- **File**: `Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`
- **Size**: ~4.9 GB
- **RAM**: 6-8 GB required
- **Why**: Excellent reasoning, good at structured output, fast

### 🥈 **Alternative: CodeLlama 7B Instruct**
- **Model**: `TheBloke/CodeLlama-7B-Instruct-GGUF`  
- **File**: `codellama-7b-instruct.Q4_K_M.gguf`
- **Size**: ~4.1 GB
- **RAM**: 5-7 GB required
- **Why**: Specialized for code/HTML analysis, very fast

### 🥉 **Lightweight: Qwen2.5 Coder 7B**
- **Model**: `bartowski/Qwen2.5-Coder-7B-Instruct-GGUF`
- **File**: `Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf`
- **Size**: ~4.2 GB
- **RAM**: 5-7 GB required
- **Why**: Great for web scraping tasks, excellent structured output

## ⚙️ **Step 3: Download Your Chosen Model**

1. **Open LM Studio**
2. **Go to "Search" tab**
3. **Search for your chosen model** (e.g., "Meta-Llama-3.1-8B-Instruct")
4. **Download the Q4_K_M version** (best quality/size balance)
5. **Wait for download** (will take a few minutes)

## 🚀 **Step 4: Start Local Server**

1. **Go to "Local Server" tab** in LM Studio
2. **Select your downloaded model**
3. **Click "Start Server"**
4. **Verify server is running** on `http://localhost:1234`

### ⚡ **Server Settings (Optional)**
- **Context Length**: 8192 (sufficient for web pages)
- **GPU Layers**: Auto (uses your GPU if available)
- **Temperature**: 0.1 (more deterministic for scraping)

## 🔧 **Step 5: Configure JobSite**

1. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** and enable local LLM:
   ```bash
   # Enable local LLM
   LOCAL_LLM_ENABLED=true
   LOCAL_LLM_BASE_URL=http://localhost:1234/v1
   LOCAL_LLM_MODEL=llama3.1:8b-instruct-q4_K_M
   LOCAL_LLM_API_KEY=lm-studio
   
   # You can leave these empty when using local LLM
   OPENAI_API_KEY=
   CLAUDE_API_KEY=
   ```

## 🧪 **Step 6: Test Your Setup**

1. **Ensure LM Studio server is running**
2. **Test basic connectivity**:
   ```bash
   source .venv/bin/activate
   ./claudia llm --ping --local
   ```

3. **Test with friendly conversation**:
   ```bash
   ./claudia llm --ping --local --hello
   ```

4. **Look for successful connection message**:
   ```
   ✓ Local LLM connection successful!
   🤖 AI Response:
      Nice to meet you! I'm an AI designed to be your go-to companion...
   ```

## 🎯 **Usage Examples**

Once configured, use JobSite normally - it will automatically use your local LLM:

```bash
# Test your local AI first
./claudia llm --ping --local --hello

# Scrape with local AI (completely private!)
./claudia scrape universal "python developer" --site indeed.com

# Discover site structure with local AI
./claudia discover jobs.apple.com

# All analysis runs locally on your machine
./claudia analyze resume ~/resume.pdf
```

## 🔧 **Troubleshooting**

### **Model Not Loading**
- **Check RAM**: Ensure you have enough RAM (6-8 GB free)
- **Try smaller model**: Use CodeLlama 7B if Llama 3.1 8B is too large
- **Close other apps**: Free up memory

### **Server Connection Issues**
- **Check LM Studio**: Ensure "Local Server" tab shows "Server Running"
- **Check port**: Default is 1234, change if needed
- **Firewall**: Ensure localhost connections are allowed

### **Slow Performance**
- **Enable GPU**: In LM Studio settings, set GPU layers to max
- **Reduce context**: Lower context length to 4096
- **Use Q4_K_M**: Don't use higher precision models (Q8, F16)

### **Poor Results**
- **Try different model**: Qwen2.5-Coder is excellent for web tasks
- **Check temperature**: Should be 0.1 for structured output
- **Update model**: Some models work better than others

## 💡 **Performance Tips**

### **Hardware Recommendations**
- **RAM**: 16GB+ (8GB minimum)
- **GPU**: Any modern GPU helps (M1/M2 Mac, RTX 3060+, etc.)
- **Storage**: SSD recommended for model loading

### **Model Size Guide**
- **7B models**: 4-6 GB RAM, good quality, fast
- **8B models**: 5-8 GB RAM, better quality, slower
- **13B+ models**: 10+ GB RAM, highest quality, much slower

### **Speed Optimization**
- **Use Q4_K_M quantization**: Best speed/quality balance
- **Enable GPU acceleration**: 5-10x speed improvement
- **Smaller context window**: Faster processing
- **Batch processing**: Process multiple pages efficiently

## 🆚 **Local vs Cloud Comparison**

| Feature | Local LLM | Claude API | OpenAI API |
|---------|-----------|------------|------------|
| **Privacy** | ✅ 100% Private | ❌ Data sent to Anthropic | ❌ Data sent to OpenAI |
| **Cost** | ✅ Free after setup | 💰 Pay per use | 💰 Pay per use |
| **Speed** | ⚡ Fast (with good hardware) | ⚡ Very Fast | ⚡ Fast |
| **Quality** | 🎯 Good (7B-8B models) | 🎯 Excellent | 🎯 Very Good |
| **Setup** | 🔧 Medium complexity | ✅ Simple (API key) | ✅ Simple (API key) |
| **Offline** | ✅ Works offline | ❌ Requires internet | ❌ Requires internet |

## 🎊 **Benefits of Local LLM**

- **🔒 Complete Privacy**: Your job searches never leave your machine
- **💰 Zero Cost**: No API fees after initial setup
- **🚀 Fast Response**: No network latency 
- **📡 Offline Capable**: Works without internet
- **🎛️ Full Control**: Adjust models, settings, prompts
- **🔄 No Rate Limits**: Scrape as much as you want

Local LLMs are perfect for JobSite because job scraping involves:
- **Sensitive career data** (privacy important)
- **High volume requests** (cost savings)
- **Structured output** (local models excel at this)
- **Repetitive tasks** (consistency important)

Start with **Llama 3.1 8B Instruct** for the best experience!