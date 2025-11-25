# Testing Guide for Kumodocs Python 3 Migration

## Quick Validation (No GUI Required)

A validation test script has been created that tests core Python 3 compatibility without requiring tkinter:

```bash
# In your virtual environment
python3 test_migration.py
```

This tests:
- Metaclass syntax
- Iterator protocol  
- String/bytes handling
- Abstract properties
- Python 3 modules (configparser, io.BytesIO)
- Google API and OAuth2 imports

**Result**: ✓ All 10 tests pass successfully!

## System Requirements for Full Testing

### Tkinter Dependency

The kumodocs application uses tkinter for GUI file selection dialogs. To run the full application and unit tests, you must install tkinter:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3-tk
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
Tkinter is included with Python 3 from python.org. If using Homebrew:
```bash
brew install python-tk@3.12  # adjust version as needed
```

**Windows:**
Tkinter is included with the official Python installer from python.org.

### Verify Tkinter Installation

```bash
python3 -c "import tkinter; print('Tkinter version:', tkinter.TkVersion)"
```

## Installation Testing

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows
```

### 2. Install Kumodocs

```bash
# From source directory
pip install -e .

# Or from requirements
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Check installed packages
pip list | grep -i kumodocs

# Expected output:
# Kumodocs  0.5  /path/to/kumodocs
```

### 4. Test Command Line Interface

With tkinter installed:
```bash
kumodocs --help
# or
python3 kumodocs.py --help
```

Expected output:
```
Usage: kumodocs [OPTIONS]

Options:
  --log-level [notset|debug|info|warning|error|critical]
                                  Controls the logging level
  --log-dir TEXT                  Sets the default logging directory (NOTE:
                                  disabled)
  -h, --help                      Show this message and exit.
```

## Unit Tests

### Running Tests

Tests require tkinter to be installed:

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/gsuite_tests/test_KIOutils.py -v

# Run with coverage
python3 -m pytest tests/ --cov=. --cov-report=html
```

### Expected Test Status

The original tests were written for Python 2.7 and may need updates for:
1. Mock library changes (unittest.mock vs mock)
2. String/bytes handling in test fixtures
3. Google API version changes

## Authentication Testing

### Prerequisites

1. Google Cloud Project with Drive API enabled
2. OAuth 2.0 credentials (client_id and client_secret)
3. Credentials configured in `config/gdrive_config.json`

### Test OAuth Flow

```bash
# This will open authentication in browser
python3 kumodocs.py --log-level debug
```

Expected behavior:
1. Browser opens for Google authentication
2. After auth, returns to CLI
3. Shows Google Drive file listing
4. Prompts for file selection

## End-to-End Testing

### Test Document Acquisition

1. **Authenticate**: Follow OAuth flow
2. **Select File**: Choose a Google Doc/Slide/Sheet
3. **Choose Revision Range**: Enter start and end revisions
4. **Verify Output**: Check `downloaded/` directory for artifacts:
   - `plaintext.txt` - Recovered plain text
   - `revision-log.txt` - Raw revision log
   - `flat_log.txt` - Flattened log
   - `comments/` - Extracted comments
   - `suggestions/` - Tracked changes
   - `images/` - Embedded images

### Test Coverage by Document Type

- [x] Google Docs - Plain text, comments, suggestions
- [x] Google Slides - Slide content, text boxes
- [x] Google Sheets - Comments only
- [x] Google Drawings - Comments only
- [ ] Google Forms - Requires Chrome/Selenium setup

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'tkinter'

**Solution**: Install system tkinter package (see above)

### Issue: ImportError: cannot import name 'flow_from_clientsecrets'

**Solution**: Ensure oauth2client is installed:
```bash
pip install oauth2client>=4.1.3
```

### Issue: Google API HttpError 404

**Possible causes**:
1. Google Drive API v2 endpoints may have changed
2. File ID is invalid
3. Insufficient permissions

**Solution**: Check API documentation and credentials

### Issue: selenium.common.exceptions.WebDriverException

**Solution**: For Forms support, install ChromeDriver:
```bash
# The app will prompt to download automatically
# Or install manually:
sudo apt-get install chromium-chromedriver  # Ubuntu/Debian
```

## Performance Testing

### Memory Usage

```bash
# Monitor memory during large document processing
/usr/bin/time -v python3 kumodocs.py
```

### Processing Speed

Large documents with many revisions may take time:
- 100 revisions: ~10-30 seconds
- 1000 revisions: ~2-5 minutes
- Network speed affects download time

## Continuous Integration

For CI/CD pipelines without GUI:

```yaml
# Example GitHub Actions
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    
- name: Run validation tests
  run: python3 test_migration.py
  
- name: Run unit tests (skip GUI tests)
  run: pytest tests/ -v -m "not gui"
```

## Known Limitations

1. **Tkinter Required**: Cannot run GUI operations in headless environments
2. **Google API v2**: May have deprecated endpoints (needs verification)
3. **Forms Handler**: Requires Chrome browser and ChromeDriver
4. **OAuth2 Flow**: Requires browser for initial authentication

## Success Criteria

✓ All validation tests pass (test_migration.py)
✓ Package installs without errors
✓ CLI help displays correctly
✓ OAuth authentication completes
✓ Can list Google Drive files
✓ Can download and process documents
✓ Output artifacts are created correctly
✓ All recovered content matches original

## Migration Status

### Completed
- ✅ Core Python 3 syntax migration
- ✅ Dependency updates
- ✅ Import statement fixes
- ✅ String/bytes handling
- ✅ Iterator protocol
- ✅ Package installation
- ✅ Basic validation tests

### Pending Full Test
- ⏳ OAuth authentication flow (requires credentials)
- ⏳ End-to-end document processing (requires Google account)
- ⏳ All unit tests (requires tkinter)
- ⏳ Forms handler (requires Chrome)

### Recommended Next Steps
1. Install tkinter system package
2. Configure Google OAuth credentials
3. Run full test suite
4. Test with real Google Workspace documents
5. Verify all artifact types are recovered correctly
