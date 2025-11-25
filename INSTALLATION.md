# Kumodocs Installation Guide (Python 3)

## Quick Start

### Option 1: Virtual Environment (Recommended)

The externally-managed-environment error occurs when trying to install packages globally on modern Linux systems. Use a virtual environment instead:

```bash
# 1. Create virtual environment
python3 -m venv kumodocs-env

# 2. Activate it
source kumodocs-env/bin/activate

# 3. Install kumodocs
pip install -e .

# 4. Run validation
python3 test_migration.py

# 5. Run application
python3 kumodocs.py --help
```

### Option 2: Using pipx (System-wide installation)

For system-wide installation without conflicts:

```bash
# Install pipx (if not already installed)
sudo apt install pipx
pipx ensurepath

# Install kumodocs
pipx install -e .

# Run from anywhere
kumodocs --help
```

### Option 3: User Installation (pip --user)

Install to your user directory:

```bash
pip install --user -e .
# or
pip install --user -r requirements.txt
```

## System Dependencies

### Install tkinter

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-tk
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
```bash
# Usually included with Python 3 from python.org
# If using Homebrew:
brew install python-tk@3.12
```

**Verify tkinter:**
```bash
python3 -c "import tkinter; print('✓ Tkinter installed')"
```

## Complete Installation Steps

### 1. Clone/Navigate to Repository

```bash
cd /path/to/kumodocs
```

### 2. Create and Activate Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate.bat
```

### 3. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Install Kumodocs

```bash
# Development installation (editable)
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### 5. Verify Installation

```bash
# Run validation tests
python3 test_migration.py

# Check package is installed
pip list | grep Kumodocs
# Expected: Kumodocs  0.5  /path/to/kumodocs

# Test CLI
python3 kumodocs.py --help
```

## Configuration

### Google OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.developers.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable Google Drive API
4. Create OAuth 2.0 Client ID (type: Desktop/Other)
5. Download credentials
6. Update `config/gdrive_config.json`:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
  }
}
```

## Usage

### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run kumodocs
python3 kumodocs.py

# With options
python3 kumodocs.py --log-level debug
```

### First Run

On first run, kumodocs will:
1. Open browser for Google authentication
2. Request Drive API permissions
3. Save credentials to `config/tokens.dat`
4. Display your Google Drive files
5. Prompt for file selection

### Subsequent Runs

After authentication, kumodocs will use saved credentials.

## Troubleshooting

### Error: externally-managed-environment

**Problem:** PEP 668 prevents installing packages globally on Debian/Ubuntu 23.04+

**Solution:** Use virtual environment (see above)

### Error: No module named 'tkinter'

**Problem:** System tkinter not installed

**Solution:**
```bash
sudo apt install python3-tk
python3 -c "import tkinter"  # verify
```

### Error: ModuleNotFoundError: No module named 'kumodocs'

**Problem:** Kumodocs not in Python path

**Solution:**
```bash
# Ensure you're in virtual environment
source venv/bin/activate

# Reinstall
pip install -e .
```

### Error: No file chosen / tkFileDialog error

**Problem:** Tkinter GUI issues

**Solutions:**
1. Verify tkinter installed: `python3 -c "import tkinter"`
2. Check DISPLAY variable: `echo $DISPLAY`
3. For SSH/remote: `ssh -X user@host` or `export DISPLAY=:0`

### Error: HttpError 403 / Insufficient permissions

**Problem:** OAuth credentials lack permissions

**Solution:**
1. Delete `config/tokens.dat`
2. Re-run kumodocs
3. Grant all requested permissions during OAuth flow

### Error: oauth2client module not found

**Problem:** Missing dependency

**Solution:**
```bash
pip install oauth2client>=4.1.3
```

## Advanced Installation

### Install with specific Python version

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

### Install from requirements.txt

```bash
pip install -r requirements.txt
# Then run directly
python3 kumodocs.py
```

### Development Installation

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Or install test dependencies
pip install pytest pytest-cov
```

### Docker Installation (Optional)

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Copy application
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Run
CMD ["python3", "kumodocs.py"]
```

## Verification Checklist

After installation, verify:

- [ ] Virtual environment activated
- [ ] `pip list | grep Kumodocs` shows version 0.5
- [ ] `python3 test_migration.py` passes all tests
- [ ] `python3 -c "import tkinter"` succeeds
- [ ] `python3 kumodocs.py --help` displays help
- [ ] Google OAuth credentials configured
- [ ] Can authenticate with Google Drive

## Quick Reference

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install
pip install -e .

# Verify
python3 test_migration.py

# Run
python3 kumodocs.py

# Deactivate venv when done
deactivate
```

## Getting Help

If you encounter issues:

1. Check this guide's troubleshooting section
2. Run validation: `python3 test_migration.py`
3. Check logs in `config/log.log`
4. Review `TESTING.md` for detailed test procedures
5. Check GitHub issues: https://github.com/kumofx/kumodocs/issues

## System Requirements

- **Python:** 3.8 or higher (tested on 3.12.3)
- **OS:** Linux, macOS, Windows
- **RAM:** 512MB minimum, 1GB recommended
- **Disk:** 100MB for application + dependencies
- **Network:** Required for Google Drive API access

## Next Steps

After successful installation:

1. Configure Google OAuth2 credentials
2. Run `python3 kumodocs.py`
3. Authenticate with Google
4. Select a document to analyze
5. Check `downloaded/` directory for results

---

**Installation complete!** The application is ready to acquire and analyze Google Workspace documents.
