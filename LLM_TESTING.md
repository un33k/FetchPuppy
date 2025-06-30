# 🔍 LLM Testing & Connectivity Guide

Test your AI provider connections and diagnose issues with JobSite's built-in LLM testing commands.

## 📋 **Quick Reference**

```bash
# Test all AI providers at once
./claudia llm --ping --all

# Test specific providers
./claudia llm --ping --local    # LM Studio (local)
./claudia llm --ping --claude   # Claude API
./claudia llm --ping --openai   # OpenAI API

# Test with friendly conversation (--hello mode)
./claudia llm --ping --local --hello    # Get AI introduction
./claudia llm --ping --claude --hello   # Conversational test
./claudia llm --ping --all --hello      # Hello to all providers

# Get help
./claudia llm --help
```

## 🎯 **Testing All Providers**

The easiest way to check your setup is to test everything at once:

```bash
./claudia llm --ping --all
```

**Example Output:**
```
Testing all AI provider connections...

==================================================
Testing Claude API connectivity...
✓ Claude API connection successful!
  Response: OK
  Response time: 1247ms
  Model: claude-3-5-sonnet-20241022
  Usage: 12 in, 1 out

==================================================
Testing OpenAI API connectivity...
✗ OpenAI API key not configured
To configure: set OPENAI_API_KEY in .env

==================================================
Testing local LLM connectivity...
✗ Local LLM connection failed: Connection error.

Troubleshooting:
  1. Is LM Studio running?
  2. Is the local server started in LM Studio?
  3. Is the model loaded?
  4. Check URL: http://localhost:1234/v1

==================================================
Connection Summary:
  ✓ Claude: Connected
  ✗ Openai: Failed
  ✗ Local: Failed

✓ 1 provider(s) available: claude
Recommendation: Claude provides the best quality for job scraping
```

## 🏠 **Testing Local LLM (LM Studio)**

Test your local LM Studio setup:

```bash
./claudia llm --ping --local
```

### **Success Example:**
```
Testing local LLM connectivity...
  URL: http://localhost:1234/v1
  Model: llama3.1:8b-instruct-q4_K_M
✓ Local LLM connection successful!
  Response: OK
  Response time: 892ms
  Model: llama-3.1-8b-instruct-q4_k_m
```

### **Common Issues:**

**❌ LM Studio Not Running:**
```
✗ Local LLM connection failed: Connection error.

Troubleshooting:
  1. Is LM Studio running?
  2. Is the local server started in LM Studio?
  3. Is the model loaded?
  4. Check URL: http://localhost:1234/v1
```
**Fix:** Start LM Studio and click "Start Server" in the Local Server tab.

**❌ Local LLM Disabled:**
```
Local LLM is disabled in configuration
To enable: set LOCAL_LLM_ENABLED=true in .env
```
**Fix:** Edit `.env` file and set `LOCAL_LLM_ENABLED=true`

## ☁️ **Testing Claude API**

Test your Claude API connection:

```bash
./claudia llm --ping --claude
```

### **Success Example:**
```
Testing Claude API connectivity...
  API Key: sk-ant-a...x4bQ
  Model: claude-3-5-sonnet-20241022
✓ Claude API connection successful!
  Response: OK
  Response time: 1247ms
  Model: claude-3-5-sonnet-20241022
  Usage: 12 in, 1 out
```

### **Common Issues:**

**❌ No API Key:**
```
Claude API key not configured
To configure: set CLAUDE_API_KEY in .env
```
**Fix:** Get API key from https://console.anthropic.com/ and add to `.env`

**❌ Invalid API Key:**
```
✗ Claude API connection failed: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}}

Troubleshooting:
  1. Check your API key is valid
  2. Check your account has credits
  3. Check internet connectivity
  4. Get API key: https://console.anthropic.com/
```
**Fix:** Verify your API key is correct and account has credits.

## 🤖 **Testing OpenAI API**

Test your OpenAI API connection:

```bash
./claudia llm --ping --openai
```

### **Success Example:**
```
Testing OpenAI API connectivity...
  API Key: sk-proj-...x8zA
  Model: gpt-4-turbo-preview
✓ OpenAI API connection successful!
  Response: OK
  Response time: 934ms
  Model: gpt-4-turbo-2024-04-09
  Usage: 13 in, 1 out
```

### **Common Issues:**

**❌ No API Key:**
```
OpenAI API key not configured
To configure: set OPENAI_API_KEY in .env
```
**Fix:** Get API key from https://platform.openai.com/api-keys and add to `.env`

**❌ Invalid API Key:**
```
✗ OpenAI API connection failed: Incorrect API key provided
```
**Fix:** Verify your API key is correct and account has credits.

## 👋 **Hello Mode - Friendly Conversation Test**

Use `--hello` with any ping command to test conversational capabilities:

### **Example: Local LLM Hello**
```bash
./claudia llm --ping --local --hello
```

**Output:**
```
Testing local LLM connectivity...
  URL: http://localhost:11434/v1
  Model: llama3.1:latest
✓ Local LLM connection successful!
  🤖 AI Response:
     Nice to meet you! I'm an AI designed to be your go-to companion for all sorts 
     of questions, topics, and tasks. My name is LLaMA, but feel free to call me 
     anything you like.

     I'm a large language model, which means I can understand and respond to natural 
     language in a way that's similar to how humans communicate. I've been trained 
     on a massive dataset of text from the internet, books, and other sources.

     What does this mean for you? Well, I can help with:
     * Answering questions on just about any topic
     * Generating ideas and creative content
     * Helping with analysis and problem-solving
     * And much more!
  Response time: 2200ms
  Model: llama3.1:latest
```

### **When to Use Hello Mode:**
- **🤖 Test conversation quality** - See how well the AI communicates
- **⚡ Check response time** - Longer responses show real performance
- **🧠 Verify model personality** - Each AI has different characteristics
- **🎯 Ensure non-streaming** - Tests complete response delivery

### **Hello vs Regular Ping:**
| Mode | Prompt | Response | Use Case |
|------|--------|----------|----------|
| **Regular** | "Say 'OK' if you can hear me." | "OK" (fast) | Quick connectivity test |
| **Hello** | "Please introduce yourself..." | Full conversation (detailed) | Quality & personality test |

## 🔧 **Configuration Setup**

### **1. Copy Environment Template**
```bash
cp .env.example .env
```

### **2. Edit Configuration**
```bash
nano .env
```

### **3. Example `.env` Configuration**

**For Cloud APIs Only:**
```bash
# AI API Keys
CLAUDE_API_KEY=sk-ant-your-claude-key-here
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Local LLM (disabled)
LOCAL_LLM_ENABLED=false
```

**For Local LLM Only:**
```bash
# AI API Keys (leave empty)
CLAUDE_API_KEY=
OPENAI_API_KEY=

# Local LLM Configuration
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:1234/v1
LOCAL_LLM_MODEL=llama3.1:8b-instruct-q4_K_M
LOCAL_LLM_API_KEY=lm-studio
```

**For All Providers:**
```bash
# AI API Keys
CLAUDE_API_KEY=sk-ant-your-claude-key-here
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Local LLM Configuration
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:1234/v1
LOCAL_LLM_MODEL=llama3.1:8b-instruct-q4_K_M
LOCAL_LLM_API_KEY=lm-studio
```

## 🚀 **Integration with Scraping**

Once your LLM tests pass, you can use JobSite's AI features:

```bash
# Use with universal scraper
./claudia scrape universal "python developer" --site indeed.com

# Discover site structure
./claudia discover jobs.apple.com

# All AI analysis will use your configured providers
```

## 🔄 **Provider Priority Order**

JobSite tries providers in this order:
1. **Claude API** (highest quality)
2. **Local LLM** (privacy + no cost)  
3. **OpenAI API** (reliable fallback)
4. **Pattern matching** (no AI fallback)

## 📊 **Understanding the Output**

### **Connection Status Icons:**
- ✅ `✓` = Connected and working
- ❌ `✗` = Failed or not configured  
- ⚠️ `⚠` = Warning (configured but issues)

### **Response Time Indicators:**
- **< 1000ms** = Excellent
- **1000-3000ms** = Good
- **> 3000ms** = Slow (may need optimization)

### **Usage Statistics:**
- **Input tokens** = Text sent to AI
- **Output tokens** = Text received from AI
- **Model** = Actual model used (may differ from requested)

## 🛠️ **Troubleshooting Checklist**

### **For All Providers:**
- [ ] Environment file exists (`.env`)
- [ ] Virtual environment activated (`source .venv/bin/activate`)
- [ ] Dependencies installed (`./bootstrap.sh`)
- [ ] Internet connectivity (for cloud APIs)

### **For Claude API:**
- [ ] Valid API key from https://console.anthropic.com/
- [ ] Account has credits
- [ ] API key in `.env` file
- [ ] No typos in API key

### **For OpenAI API:**
- [ ] Valid API key from https://platform.openai.com/api-keys
- [ ] Account has credits  
- [ ] API key in `.env` file
- [ ] No typos in API key

### **For Local LLM:**
- [ ] LM Studio installed and running
- [ ] Model downloaded in LM Studio
- [ ] Local server started in LM Studio
- [ ] `LOCAL_LLM_ENABLED=true` in `.env`
- [ ] Correct URL (default: `http://localhost:1234/v1`)

## 🎯 **Quick Setup Commands**

**Complete setup from scratch:**
```bash
# 1. Setup environment
./bootstrap.sh

# 2. Configure API keys
cp .env.example .env
nano .env  # Add your API keys

# 3. Test everything
source .venv/bin/activate
./claudia llm --ping --all

# 4. Start scraping!
./claudia scrape universal "software engineer" --site indeed.com
```

**Just test without setup:**
```bash
source .venv/bin/activate
./claudia llm --ping --all
```

## 📚 **Complete Command Reference**

### **Basic Connectivity Tests**
```bash
./claudia llm --ping --local       # Test local LLM only
./claudia llm --ping --claude      # Test Claude API only  
./claudia llm --ping --openai      # Test OpenAI API only
./claudia llm --ping --all         # Test all providers
```

### **Conversation Tests (Hello Mode)**
```bash
./claudia llm --ping --local --hello    # Local LLM conversation
./claudia llm --ping --claude --hello   # Claude conversation
./claudia llm --ping --openai --hello   # OpenAI conversation  
./claudia llm --ping --all --hello      # All providers conversation
```

### **Getting Help**
```bash
./claudia llm                      # Show LLM command help
./claudia llm --help               # Full LLM help documentation
./claudia --help                   # Complete Claudia help
./claudia --examples               # Usage examples
```

### **Example Workflow**
```bash
# 1. Test everything with conversation
./claudia llm --ping --all --hello

# 2. If local LLM works, test job scraping
./claudia scrape universal "test job" --site indeed.com --max-results 2

# 3. Check what jobs were found
./claudia export --format json

# 4. Ready for real job searching!
./claudia scrape universal "your dream job" --site your-favorite-site.com
```

## 💡 **Pro Tips**

1. **Start with `--hello`** to test conversation quality and performance
2. **Use local LLM** for privacy and cost savings
3. **Claude gives best results** for job scraping
4. **OpenAI is reliable** as a fallback option
5. **Test regularly** to catch API key expiration
6. **Check response times** to optimize performance
7. **Hello mode shows personality** - see how each AI communicates differently

Need help? Check `./claudia --help` or `./claudia --examples` for more information!