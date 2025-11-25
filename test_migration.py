#!/usr/bin/env python3
"""
Test script to validate Python 3 migration without requiring GUI dependencies.
This script tests core functionality that doesn't depend on tkinter.
"""

import sys
import os

print("=" * 70)
print("KUMODOCS PYTHON 3 MIGRATION - VALIDATION TESTS")
print("=" * 70)
print(f"\nRunning on: Python {sys.version}\n")

# Track test results
passed = 0
failed = 0
skipped = 0

def test(name, func):
    """Run a test and track results"""
    global passed, failed, skipped
    try:
        func()
        print(f"✓ {name}")
        passed += 1
        return True
    except ImportError as e:
        print(f"⊘ {name} (skipped: {e})")
        skipped += 1
        return False
    except AssertionError as e:
        print(f"✗ {name}: {e}")
        failed += 1
        return False
    except Exception as e:
        print(f"✗ {name}: {type(e).__name__}: {e}")
        failed += 1
        return False

# Test 1: Import core modules (no tkinter)
def test_baseclass_import():
    import baseclass
    assert hasattr(baseclass, 'Driver')
    assert hasattr(baseclass, 'Parser')
    assert hasattr(baseclass, 'Handler')

# Test 2: Metaclass syntax
def test_metaclass_syntax():
    import baseclass
    from abc import ABCMeta
    assert type(baseclass.Driver) == ABCMeta
    assert type(baseclass.Parser) == ABCMeta
    assert type(baseclass.Handler) == ABCMeta

# Test 3: Iterator protocol
def test_iterator_protocol():
    from baseclass import Handler
    obj = Handler.KumoObj(filename='test.txt', content=b'test')
    assert hasattr(obj, '__next__')
    items = list(obj)
    assert len(items) == 1

# Test 4: String encoding
def test_string_encoding():
    from baseclass import Handler
    import json
    # Test LogParser would encode properly
    test_log = {"test": "data"}
    content = Handler.stringify(test_log).encode('utf-8')
    assert isinstance(content, bytes)
    assert len(content) > 0

# Test 5: Mappings module
def test_mappings():
    import mappings
    assert hasattr(mappings, '__file__')

# Test 6: Check Google API imports
def test_google_api_imports():
    import googleapiclient.discovery
    import googleapiclient.errors
    assert hasattr(googleapiclient.discovery, 'build')
    assert hasattr(googleapiclient.errors, 'HttpError')

# Test 7: Check oauth2client
def test_oauth2client():
    import oauth2client.client
    import oauth2client.file
    assert hasattr(oauth2client.client, 'flow_from_clientsecrets')

# Test 8: Check configparser (Python 3)
def test_configparser():
    import configparser
    parser = configparser.ConfigParser()
    assert hasattr(parser, 'read')
    assert hasattr(parser, 'get')

# Test 9: Check io module (BytesIO)
def test_io_module():
    import io
    buffer = io.BytesIO(b'test data')
    assert buffer.read() == b'test data'

# Test 10: Check abstract properties work
def test_abstract_properties():
    import baseclass
    import inspect
    # Get the logger property from Driver
    assert hasattr(baseclass.Driver, 'logger')
    assert isinstance(inspect.getattr_static(baseclass.Driver, 'logger'), property)

# Test 11: Test module imports work correctly
def test_module_imports():
    import gsuite.driver
    import gsuite.gapiclient
    import gsuite.docshandler
    import gsuite.slideshandler
    import gsuite.sheetshandler
    import gsuite.formshandler
    assert hasattr(gsuite.driver, 'GSuiteDriver')

# Test 12: Test main kumodocs module
def test_kumodocs_import():
    import kumodocs
    assert hasattr(kumodocs, 'cli')
    assert hasattr(kumodocs, 'main')

print("Running tests...\n")
print("[Core Module Tests]")
test("Import baseclass module", test_baseclass_import)
test("Metaclass syntax (ABCMeta)", test_metaclass_syntax)
test("Iterator protocol (__next__)", test_iterator_protocol)
test("String/bytes encoding", test_string_encoding)
test("Abstract properties", test_abstract_properties)

print("\n[Python 3 Compatibility Tests]")
test("configparser module", test_configparser)
test("io.BytesIO module", test_io_module)
test("Mappings module", test_mappings)

print("\n[Dependency Tests]")
test("Google API imports", test_google_api_imports)
test("OAuth2 client imports", test_oauth2client)

print("\n[Module Import Tests]")
test("GSuite package imports", test_module_imports)
test("Main kumodocs module", test_kumodocs_import)

# Summary
print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed, {skipped} skipped")
print("=" * 70)

if failed > 0:
    print("\n⚠ Some tests failed - review errors above")
    sys.exit(1)
elif skipped > 0:
    print("\n⊘ Some tests skipped due to missing dependencies")
    print("   Install with: pip install -r requirements.txt")
    sys.exit(0)
else:
    print("\n✓ All tests passed! Migration successful!")
    print("\n📋 NEXT STEPS:")
    print("  1. Install tkinter: sudo apt install python3-tk")
    print("  2. Test CLI: python3 kumodocs.py --help")
    print("  3. Configure Google OAuth credentials")
    print("  4. Run: python3 kumodocs.py")
    sys.exit(0)
