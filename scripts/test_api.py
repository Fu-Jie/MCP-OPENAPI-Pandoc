#!/usr/bin/env python3
"""Test script for Pandoc Bridge API."""

import json
import subprocess
import sys
import urllib.request
from urllib.error import HTTPError, URLError

BASE_URL = "http://localhost:3411"


def get_token() -> str:
    """Get API key from container environment or generate test key."""
    # Try to get from container's environment
    result = subprocess.run(
        ["docker", "exec", "pandoc-bridge", "python", "-c",
         "from src.config import get_settings; "
         "keys = get_settings().get_api_keys(); "
         "print(list(keys.keys())[0] if keys else '')"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    
    print("   ⚠️  No API key configured, some tests may fail")
    return "sk-test-key"


def request(method: str, path: str, data: dict | None = None, token: str | None = None) -> dict:
    """Make HTTP request to API."""
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        return json.loads(e.read().decode())
    except URLError as e:
        return {"error": str(e)}


def test_health():
    """Test health endpoint."""
    print("\n🔍 Testing /health...")
    result = request("GET", "/health")
    
    if result.get("status") == "healthy":
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Pandoc: {result['pandoc_version']}")
        return True
    else:
        print(f"   ❌ Failed: {result}")
        return False


def test_service_info():
    """Test service info endpoint."""
    print("\n🔍 Testing /...")
    result = request("GET", "/")
    
    if result.get("name") == "pandoc-bridge":
        print(f"   ✅ Name: {result['name']}")
        print(f"   ✅ Version: {result['version']}")
        print(f"   ✅ Endpoints: {len(result['endpoints'])} available")
        return True
    else:
        print(f"   ❌ Failed: {result}")
        return False


def test_formats():
    """Test formats endpoint."""
    print("\n🔍 Testing /api/v1/formats...")
    result = request("GET", "/api/v1/formats")
    
    if "input" in result and "output" in result:
        print(f"   ✅ Input formats: {len(result['input'])}")
        print(f"   ✅ Output formats: {len(result['output'])}")
        return True
    else:
        print(f"   ❌ Failed: {result}")
        return False


def test_auth_required():
    """Test that convert endpoint requires auth."""
    print("\n🔍 Testing auth requirement...")
    result = request("POST", "/api/v1/convert/text", {
        "content": "# Test",
        "from_format": "markdown",
        "to_format": "html"
    })
    
    if result.get("error", {}).get("code") == "UNAUTHORIZED":
        print("   ✅ Correctly rejected without token")
        return True
    else:
        print(f"   ❌ Expected UNAUTHORIZED, got: {result}")
        return False


def test_convert_text(token: str):
    """Test text conversion."""
    print("\n🔍 Testing /api/v1/convert/text...")
    result = request("POST", "/api/v1/convert/text", {
        "content": "# Hello World\n\nThis is **bold** text.",
        "from_format": "markdown",
        "to_format": "html"
    }, token)
    
    if "content" in result and "<h1" in result["content"]:
        print("   ✅ Markdown → HTML conversion successful")
        print(f"   ✅ Content type: {result['content_type']}")
        return True
    else:
        print(f"   ❌ Failed: {result}")
        return False


def test_convert_latex(token: str):
    """Test LaTeX conversion."""
    print("\n🔍 Testing Markdown → LaTeX...")
    result = request("POST", "/api/v1/convert/text", {
        "content": "# Title\n\n## Section\n\nParagraph with $E=mc^2$ equation.",
        "from_format": "markdown",
        "to_format": "latex"
    }, token)
    
    if "content" in result and "\\section" in result["content"]:
        print("   ✅ Markdown → LaTeX conversion successful")
        return True
    else:
        print(f"   ❌ Failed: {result}")
        return False


def test_convert_rst(token: str):
    """Test RST conversion."""
    print("\n🔍 Testing HTML → RST...")
    result = request("POST", "/api/v1/convert/text", {
        "content": "<h1>Title</h1><p>Paragraph</p><ul><li>Item 1</li><li>Item 2</li></ul>",
        "from_format": "html",
        "to_format": "rst"
    }, token)
    
    if "content" in result:
        print("   ✅ HTML → RST conversion successful")
        return True
    else:
        print(f"   ❌ Failed: {result}")
        return False


def test_invalid_format(token: str):
    """Test invalid format handling."""
    print("\n🔍 Testing invalid format error...")
    result = request("POST", "/api/v1/convert/text", {
        "content": "test",
        "from_format": "invalid_format",
        "to_format": "html"
    }, token)
    
    if result.get("error", {}).get("code") == "FORMAT_NOT_SUPPORTED":
        print("   ✅ Correctly rejected invalid format")
        return True
    else:
        print(f"   ❌ Expected FORMAT_NOT_SUPPORTED, got: {result}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("🚀 Pandoc Bridge API Test Suite")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    
    # Get token
    print("\n🔑 Getting test token...")
    token = get_token()
    print(f"   ✅ Token obtained (length: {len(token)})")
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Service Info", test_service_info()))
    results.append(("Formats List", test_formats()))
    results.append(("Auth Required", test_auth_required()))
    results.append(("Convert Text", test_convert_text(token)))
    results.append(("Convert LaTeX", test_convert_latex(token)))
    results.append(("Convert RST", test_convert_rst(token)))
    results.append(("Invalid Format", test_invalid_format(token)))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
