#!/usr/bin/env python
"""Export OpenAPI specification from the FastAPI application."""

import json
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    """Export OpenAPI spec to a JSON file."""
    output_path = Path("public/openapi.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from src.main import app

        openapi_spec = app.openapi()
    except ImportError as e:
        print(f"Error importing FastAPI app: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating OpenAPI spec: {e}", file=sys.stderr)
        sys.exit(1)

    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)

    print(f"OpenAPI specification exported to {output_path}")


if __name__ == "__main__":
    main()
