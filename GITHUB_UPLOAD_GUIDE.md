# 📤 GitHub Upload Guide for MP4 Transcriber

This guide will help you publish your MP4 Transcriber project to GitHub.

---

## 🎯 Quick Upload (3 Steps)

### 1️⃣ Run the Setup Script

```powershell
# Navigate to project folder
cd C:\Projects\Whisper-ASR

# Run the automated setup script
.\setup-github.ps1
```

This script will:
- Initialize Git repository
- Add all files
- Create initial commit
- Set branch name to 'main'

### 2️⃣ Create Repository on GitHub

1. Go to https://github.com/new
2. Fill in:
   - **Repository name:** `mp4-transcriber`
   - **Description:** "Automated video transcription tool using OpenAI Whisper and ffmpeg"
   - **Visibility:** Public (recommended) or Private
   - **DO NOT check:** "Add a README file", "Add .gitignore", "Add a license"
3. Click **"Create repository"**

### 3️⃣ Push to GitHub

Copy the commands from GitHub and run them in PowerShell:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/mp4-transcriber.git
git push -u origin main
```

**Important:** Replace `YOUR_USERNAME` with your actual GitHub username!

---

## 📋 Manual Step-by-Step Instructions

If you prefer to do it manually:

### Step 1: Verify Git Installation

```powershell
git --version
```

If not installed, download from https://git-scm.com/

### Step 2: Initialize Git Repository

```powershell
cd C:\Projects\Whisper-ASR
git init
```

You should see: `Initialized empty Git repository in...`

### Step 3: Check .gitignore

Your `.gitignore` is already configured to exclude:
- `videos/` folder (your input videos)
- `transcripts/` folder (output files)
- `.env` file (your configuration)
- `__pycache__/` folders
- Python compiled files

Verify it exists:
```powershell
cat .gitignore
```

### Step 4: Stage All Files

```powershell
git add .
```

### Step 5: Verify Staged Files

```powershell
git status
```

You should see files under "Changes to be committed".

### Step 6: Create Initial Commit

```powershell
git commit -m "Initial commit: MP4 Transcriber v1.0"
```

### Step 7: Set Branch Name

```powershell
git branch -M main
```

### Step 8: Create GitHub Repository

1. Go to https://github.com/new
2. Enter repository details:
   - **Name:** `mp4-transcriber`
   - **Description:** "Python application for automated video transcription using Whisper ASR"
   - **Public** (recommended for open source)
   - Leave all initialization options **UNCHECKED**

3. Click **"Create repository"**

### Step 9: Connect Local to Remote

GitHub will show you commands like:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/mp4-transcriber.git
git push -u origin main
```

Run these commands in your PowerShell.

### Step 10: Verify Upload

```powershell
git remote -v
```

You should see your GitHub repository URL.

```powershell
git log --oneline
```

You should see your commit.

---

## 🔧 Troubleshooting

### Issue: "fatal: remote origin already exists"

**Solution:**
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/mp4-transcriber.git
git push -u origin main
```

### Issue: "fatal: Authentication failed"

**Solutions:**

**Option 1: Use Personal Access Token**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Use token instead of password:
   ```
   Username: YOUR_USERNAME
   Password: YOUR_TOKEN
   ```

**Option 2: Use SSH (Recommended for frequent use)**
```powershell
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add key to GitHub
# 1. Copy public key
cat ~/.ssh/id_ed25519.pub
# 2. Go to GitHub Settings → SSH and GPG keys → New SSH key
# 3. Paste your key

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/mp4-transcriber.git
git push -u origin main
```

### Issue: Files are too large

Git has a 100MB file size limit on GitHub. Your `.gitignore` should prevent this, but check:

```powershell
# See file sizes in repository
git ls-files -s | Sort-Object -Property Size -Descending

# If large files were accidentally committed:
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch PATH_TO_LARGE_FILE" \
  --prune-empty --tag-name-filter cat -- --all
git push origin --force --all
```

### Issue: "Updates were rejected because the remote contains work that you do not have"

This happens if you initialized GitHub repo with README/.gitignore.

**Solution:**
```powershell
git pull origin main --allow-unrelated-histories
git push -u origin main
```

---

## 📊 What Gets Uploaded

### ✅ Included Files:
- `main.py` - CLI interface
- `transcriber.py` - Core logic
- `batch_processor.py` - Batch processing
- `config.py` - Configuration
- `utils/` - Utility modules
- `tests/` - Unit tests
- `requirements.txt` - Dependencies
- `.env.example` - Config template
- `.gitignore` - Git ignore rules
- `README.md` - Main documentation
- `SETUP_GUIDE.md` - Installation guide
- `QUICK_REFERENCE.md` - Quick reference
- `INSTALLATION_CHECKLIST.md` - Setup checklist
- `PROJECT_SUMMARY.md` - Implementation summary
- `verify_imports.py` - Import verification
- `setup-github.ps1` - This setup script

### ❌ Excluded Files (by .gitignore):
- `videos/` folder
- `transcripts/` folder
- `.env` file
- `__pycache__/` folders
- `*.pyc` files
- IDE files (`.vscode/`, `.idea/`)

---

## 🎨 Post-Upload Enhancements

### 1. Add Repository Topics

On GitHub, go to your repository → About section → Add topics:
- `python`
- `whisper`
- `transcription`
- `ffmpeg`
- `asr`
- `speech-to-text`
- `openai`
- `video-processing`

### 2. Add GitHub Actions CI/CD (Optional)

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python tests/test_transcriber.py
```

### 3. Add License (Optional)

Choose a license at https://choosealicense.com/ and add `LICENSE` file.

### 4. Enable GitHub Discussions (Optional)

For community support, enable Discussions in repository Settings.

---

## 📈 Repository Statistics

After uploading, you can view:
- **Traffic:** Insights → Traffic (views, clones)
- **Contributors:** Insights → Contributors
- **Commits:** Insights → Commits
- **Network:** Insights → Network (forks)

---

## 🔄 Updating Your Repository

After making changes:

```powershell
# Check what changed
git status

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

---

## 🎯 Best Practices

### Commit Messages
- Use clear, descriptive messages
- Start with verb (Add, Fix, Update, Remove)
- Reference issues: `Fixes #123`

Example:
```bash
git commit -m "Add error handling for missing video files"
```

### Branching (for larger changes)
```bash
# Create feature branch
git checkout -b feature/new-format-support

# Make changes and commit
git add .
git commit -m "Add VTT export format"

# Push branch
git push origin feature/new-format-support

# Create Pull Request on GitHub
```

### Tags for Releases
```bash
# Create version tag
git tag -a v1.0.0 -m "Version 1.0.0 - Initial release"
git push origin --tags
```

---

## 📞 Need Help?

- **Git Documentation:** https://git-scm.com/doc
- **GitHub Docs:** https://docs.github.com
- **Git Handbook:** https://guides.github.com/introduction/git-handbook/

---

## ✅ Success Checklist

- [ ] Git repository initialized locally
- [ ] All files staged and committed
- [ ] GitHub repository created
- [ ] Remote added successfully
- [ ] Files pushed to GitHub
- [ ] Repository visible on GitHub
- [ ] README renders correctly
- [ ] No sensitive data uploaded (.env excluded)
- [ ] No large files (>100MB) uploaded

---

**🎉 Congratulations!** Your MP4 Transcriber is now on GitHub and ready to share with the world!
