"""Make the ats_resolver_mcp package importable when running pytest from this directory."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
