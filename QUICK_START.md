# 🚀 JobSite Quick Start Guide

Get JobSite up and running in 5 minutes with these simple commands.

## ⚡ **Super Quick Setup**

```bash
# 1. Setup environment
./bootstrap.sh
source .venv/bin/activate

# 2. Configure AI (choose one option)
cp .env.example .env
# Then edit .env with your preferred AI setup

# 3. Test AI connectivity
./claudia llm --ping --all

# 4. Initialize database
./claudia database --init

# 5. Start scraping!
./claudia scrape universal "python developer" --site indeed.com
```

## 🎯 **Essential Commands to Run**

### **First Time Setup**
```bash
# Setup Python environment and dependencies
./bootstrap.sh

# Activate virtual environment (run every session)
source .venv/bin/activate

# Copy configuration template
cp .env.example .env
```

### **AI Configuration Test**
```bash
# Test all AI providers - RUN THIS FIRST!
./claudia llm --ping --all

# Test specific providers
./claudia llm --ping --local    # Local LLM (LM Studio)
./claudia llm --ping --claude   # Claude API
./claudia llm --ping --openai   # OpenAI API

# Test with friendly conversation (recommended!)
./claudia llm --ping --local --hello    # See AI personality & quality
./claudia llm --ping --all --hello      # Test all with conversation
```

### **Database Setup**
```bash
# Initialize database (first time only)
./claudia database --init

# Check database status
./claudia database --stats
```

### **Job Scraping**
```bash
# Universal AI-powered scraping (works with any site)
./claudia scrape universal "software engineer" --site indeed.com
./claudia scrape universal "data scientist" --site linkedin.com/jobs --location "remote"

# Discover site structure with AI
./claudia discover jobs.apple.com
./claudia discover careers.google.com
```

### **Data Export**
```bash
# Export scraped jobs
./claudia export --format json
./claudia export --format csv --filter remote
```

## 🔧 **AI Provider Setup Options**

### **Option 1: Local LLM (Recommended - Private & Free)**
```bash
# 1. Install LM Studio from https://lmstudio.ai/
# 2. Follow LM_STUDIO_SETUP.md for detailed setup
# 3. Configure in .env:
echo "LOCAL_LLM_ENABLED=true" >> .env

# 4. Test connection:
./claudia llm --ping --local
```

### **Option 2: Claude API (Best Quality)**
```bash
# 1. Get API key from https://console.anthropic.com/
# 2. Add to .env:
echo "CLAUDE_API_KEY=your_claude_key_here" >> .env

# 3. Test connection:
./claudia llm --ping --claude
```

### **Option 3: OpenAI API (Reliable Fallback)**
```bash
# 1. Get API key from https://platform.openai.com/api-keys
# 2. Add to .env:
echo "OPENAI_API_KEY=your_openai_key_here" >> .env

# 3. Test connection:
./claudia llm --ping --openai
```

## 🎪 **Demo Commands to Try**

### **Test with Real Sites**
```bash
# Major job sites (AI will adapt automatically)
./claudia scrape universal "python developer" --site indeed.com --max-results 5
./claudia scrape universal "remote work" --site weworkremotely.com --max-results 3
./claudia discover stackoverflow.com/jobs
```

### **Check Everything is Working**
```bash
# Complete system check
./claudia llm --ping --all --hello  # AI connectivity + conversation test
./claudia database --stats          # Database status
./claudia export --format json      # Data export
```

## 🆘 **Troubleshooting**

### **If AI Tests Fail**
```bash
# Check configuration
cat .env

# Check available commands
./claudia --help

# Get detailed help
./claudia llm --help
```

### **Common Issues**

**"No AI providers available"**
- Solution: Configure at least one AI provider in `.env` file
- See LLM_TESTING.md for detailed diagnostics

**"Local LLM connection failed"**
- Solution: Install and start LM Studio server
- See LM_STUDIO_SETUP.md for complete setup guide

**"Claude/OpenAI API failed"**
- Solution: Check API key is valid and account has credits
- Get keys from provider websites

## 📚 **Next Steps**

Once everything is working:

1. **Read the docs:**
   - `LLM_TESTING.md` - AI connectivity testing
   - `LM_STUDIO_SETUP.md` - Local LLM setup
   - `README.md` - Complete feature overview

2. **Explore features:**
   ```bash
   ./claudia --examples  # See all available commands
   ./claudia --help      # Full command reference
   ```

3. **Start scraping jobs:**
   ```bash
   ./claudia scrape universal "your dream job" --site your-favorite-job-site.com
   ```

## 🎉 **Success Indicators**

You'll know everything is working when:

- ✅ `./claudia llm --ping --all --hello` shows at least one provider with friendly response
- ✅ `./claudia database --stats` shows database initialized  
- ✅ `./claudia scrape universal "test" --site indeed.com` finds some jobs
- ✅ `./claudia export --format json` creates an export file

**Ready to find your dream job? Start scraping! 🚀**