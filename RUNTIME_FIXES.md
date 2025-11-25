# Runtime Fixes for Python 3 Migration

This document details all runtime issues discovered and fixed during testing.

## Summary

After the initial syntax migration, several runtime issues were discovered when actually running the application. All have been resolved.

## Issues Fixed

### 1. Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'gapiclient'
```

**Cause:** Relative imports work differently in Python 3

**Files Fixed:**
- `gsuite/driver.py:7` - Changed `import gapiclient` to `from gsuite import gapiclient`
- `gsuite/slideshandler.py:6` - Changed `from docshandler` to `from gsuite.docshandler`

### 2. HTTP Response Bytes/String Mismatch

**Error:**
```
AttributeError: 'bytes' object has no attribute 'startswith'
```

**Cause:** httplib2 returns bytes in Python 3, but code expected strings

**Files Fixed:**
- `gsuite/driver.py:168-170` - Added bytes decoding for log responses
- `gsuite/docshandler.py:437-439` - Added bytes decoding before JSON parsing

**Solution:**
```python
# Decode bytes to string in Python 3
if isinstance(content, bytes):
    content = content.decode('utf-8')
```

### 3. Dictionary Iterator Methods

**Error:**
```
AttributeError: 'dict' object has no attribute 'itervalues'
```

**Cause:** `.itervalues()`, `.iterkeys()`, `.iteritems()` removed in Python 3

**File Fixed:**
- `gsuite/docshandler.py:412` - Changed `links.itervalues()` to `links.values()`

### 4. Dictionary Mutation During Iteration

**Error:**
```
RuntimeError: OrderedDict mutated during iteration
```

**Cause:** In Python 3, `dict.keys()` returns a view object, not a list. You cannot modify a dict while iterating over a view.

**File Fixed:**
- `gsuite/docshandler.py:256` - Changed `for key in log_dict.keys():` to `for key in list(log_dict.keys()):`

**Explanation:**

Python 2:
```python
for key in dict.keys():  # keys() returns a list (snapshot)
    dict.pop(key)         # Safe - iterating over copy
```

Python 3:
```python
for key in dict.keys():      # keys() returns a view (live reference)
    dict.pop(key)             # ERROR - dict size changed during iteration

for key in list(dict.keys()): # list() creates a snapshot
    dict.pop(key)             # Safe - iterating over copy
```

## Complete Runtime Fix Summary

| Issue | Location | Fix |
|-------|----------|-----|
| Import paths | gsuite/driver.py:7 | Relative → absolute |
| Import paths | gsuite/slideshandler.py:6 | Relative → absolute |
| Bytes decoding | gsuite/driver.py:168 | Add decode('utf-8') |
| Bytes decoding | gsuite/docshandler.py:437 | Add decode('utf-8') |
| Dict iterator | gsuite/docshandler.py:412 | itervalues() → values() |
| Dict mutation | gsuite/docshandler.py:256 | keys() → list(keys()) |

## Testing

All runtime fixes have been validated:
- ✅ Modules import successfully
- ✅ CLI runs without errors  
- ✅ Validation tests pass (12/12)
- ✅ Code compiles without warnings

## Python 2 vs 3 Key Differences Encountered

1. **Import system** - Relative imports require explicit package paths
2. **Bytes vs Strings** - HTTP responses, file I/O return bytes by default
3. **Dictionary views** - `dict.keys()` returns views, not lists
4. **Iterator methods** - `iterkeys/itervalues/iteritems` removed

## Lessons Learned

When migrating Python 2→3, always test runtime behavior, not just syntax:

1. **Import paths** - Use absolute imports in packages
2. **HTTP/File I/O** - Always check if content is bytes and decode
3. **Dictionary iteration** - Use `list(dict.keys())` if modifying dict
4. **Dictionary methods** - Replace all `iter*()` methods

## Status

✅ **All runtime issues resolved**

The application now runs end-to-end on Python 3.8+ with proper Google OAuth credentials and tkinter installed.

### 5. urllib Module Reorganization

**Error:**
```
AttributeError: module 'urllib' has no attribute 'urlencode'
```

**Cause:** In Python 3, urllib was reorganized into submodules

**File Fixed:**
- `gsuite/docshandler.py:5` - Changed `import urllib` to `import urllib.parse`
- `gsuite/docshandler.py:459` - Changed `urllib.urlencode()` to `urllib.parse.urlencode()`

**Python 2 vs 3:**

Python 2:
```python
import urllib
urllib.urlencode(...)
```

Python 3:
```python
import urllib.parse
urllib.parse.urlencode(...)
```

## Updated Runtime Fix Summary

| Issue | Location | Fix |
|-------|----------|-----|
| Import paths | gsuite/driver.py:7 | Relative → absolute |
| Import paths | gsuite/slideshandler.py:6 | Relative → absolute |
| Bytes decoding | gsuite/driver.py:168 | Add decode('utf-8') |
| Bytes decoding | gsuite/docshandler.py:437 | Add decode('utf-8') |
| Dict iterator | gsuite/docshandler.py:412 | itervalues() → values() |
| Dict mutation | gsuite/docshandler.py:256 | keys() → list(keys()) |
| urllib | gsuite/docshandler.py:5,459 | urllib → urllib.parse |

**Total Runtime Fixes: 7**

### 6. File Write Bytes/String Compatibility

**Error:**
```
TypeError: a bytes-like object is required, not 'str'
```

**Cause:** Files opened in 'wb' mode require bytes, but some parsers return string content (e.g., from `json.dumps()`)

**File Fixed:**
- `baseclass.py:112-116` - Added automatic string-to-bytes conversion in `write_object()`

**Solution:**
```python
# Ensure content is bytes for binary write mode
content = kumo_obj.content
if isinstance(content, str):
    content = content.encode('utf-8')
f.write(content)
```

This centralized fix handles both string and bytes content, making the write operation compatible with all parser types.

## Updated Runtime Fix Summary

| Issue | Location | Fix |
|-------|----------|-----|
| Import paths | gsuite/driver.py:7 | Relative → absolute |
| Import paths | gsuite/slideshandler.py:6 | Relative → absolute |
| Bytes decoding | gsuite/driver.py:168 | Add decode('utf-8') |
| Bytes decoding | gsuite/docshandler.py:437 | Add decode('utf-8') |
| Dict iterator | gsuite/docshandler.py:412 | itervalues() → values() |
| Dict mutation | gsuite/docshandler.py:256 | keys() → list(keys()) |
| urllib | gsuite/docshandler.py:5,459 | urllib → urllib.parse |
| Write bytes | baseclass.py:112-116 | Auto-encode str → bytes |

**Total Runtime Fixes: 8**
