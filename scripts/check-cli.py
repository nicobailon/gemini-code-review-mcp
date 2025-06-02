#!/usr/bin/env python3
"""
CLI Discovery and Diagnostic Script

Helps users identify which CLI commands are available and diagnose common issues.
"""

import subprocess
import os
from pathlib import Path
from typing import Any, Tuple, List

def check_command_availability() -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Check which CLI commands are available."""
    print("🔍 Checking CLI Command Availability...\n")
    
    commands: List[Tuple[str, str]] = [
        ("gemini-code-review-mcp", "Main CLI (installed package)"),
        ("generate-code-review", "Context generation CLI (installed package)"),
        ("generate-meta-prompt", "Meta-prompt CLI (installed package)")
    ]
    
    available: List[Tuple[str, str]] = []
    unavailable: List[Tuple[str, str]] = []
    
    for cmd, description in commands:
        try:
            result = subprocess.run([cmd, "--help"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                available.append((cmd, description))
                print(f"✅ {cmd} - {description}")
            else:
                unavailable.append((cmd, description))
                print(f"❌ {cmd} - {description} (exit code: {result.returncode})")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            unavailable.append((cmd, description))
            print(f"❌ {cmd} - {description} (not found)")
    
    return available, unavailable

def check_development_mode() -> None:
    """Check if development mode commands work."""
    print("\n🔧 Checking Development Mode Commands...\n")
    
    dev_commands = [
        (["python3", "-m", "src.cli_main", "--help"], "Main CLI (development)"),
        (["python3", "-m", "src.meta_prompt_generator", "--help"], "Meta-prompt CLI (development)")
    ]
    
    for cmd, description in dev_commands:
        try:
            result = subprocess.run(cmd, 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} (exit code: {result.returncode})")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"❌ {description} (error: {e})")

def check_package_version() -> None:
    """Check installed package version vs local version."""
    print("\n📦 Checking Package Versions...\n")
    
    # Check local pyproject.toml version
    local_version: str = "unknown"
    try:
        # Handle tomllib import for different Python versions
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib  # Python 3.10 and earlier
            except ImportError:
                raise ImportError("Neither tomllib nor tomli available for TOML parsing")
        
        with open("pyproject.toml", "rb") as f:
            data: dict[str, Any] = tomllib.load(f)
            local_version: str = data["project"]["version"]
            print(f"📁 Local version (pyproject.toml): {local_version}")
    except Exception as e:
        print(f"❌ Could not read local version: {e}")
        local_version = "unknown"
    
    # Check installed package version
    try:
        result = subprocess.run(["pip", "show", "gemini-code-review-mcp"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    installed_version = line.split(':', 1)[1].strip()
                    print(f"📦 Installed version: {installed_version}")
                    
                    if local_version != "unknown" and installed_version != local_version:
                        print(f"⚠️  Version mismatch! Local: {local_version}, Installed: {installed_version}")
                        print("   Consider: pip install -e . (for development)")
                    break
        else:
            print("❌ Package not installed via pip")
    except Exception as e:
        print(f"❌ Could not check installed version: {e}")

def provide_recommendations():
    """Provide recommendations based on findings."""
    print("\n💡 Recommendations:\n")
    
    print("🎯 For Users:")
    print("   • Use: uvx gemini-code-review-mcp /path/to/project")
    print("   • If issues: uv cache clean && uvx --force gemini-code-review-mcp")
    print()
    
    print("🔧 For Developers:")
    print("   • Use: python -m src.cli_main /path/to/project")
    print("   • Install development mode: pip install -e .")
    print("   • Test meta-prompts: python -m src.meta_prompt_generator --help")
    print()
    
    print("🚨 If Nothing Works:")
    print("   • Check API key: export GEMINI_API_KEY=your_key")
    print("   • Check .env file exists and contains GEMINI_API_KEY")
    print("   • Try: python -m src.generate_code_review_context --help")

def main():
    """Run all diagnostic checks."""
    print("🔍 CLI Diagnostic Tool")
    print("=" * 50)
    
    # Change to script directory to ensure we're in the right place
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    check_command_availability()
    check_development_mode()
    check_package_version()
    provide_recommendations()
    
    print("\n" + "=" * 50)
    print("✅ Diagnostic complete!")

if __name__ == "__main__":
    main()