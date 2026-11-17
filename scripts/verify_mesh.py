"""Clean and verify an STL mesh: report degenerate faces and watertightness.

Usage:

    python scripts/verify_mesh.py path/to/model.stl

Prints a JSON-ish summary and exits non-zero unless the raw mesh is watertight
with positive volume.
"""

import json
import sys

import trimesh


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/verify_mesh.py <file.stl>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    mesh = trimesh.load(path)

    nondegen = mesh.nondegenerate_faces()
    n_degenerate = len(mesh.faces) - len(nondegen)

    result = {
        "file": path,
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
        "degenerate_faces": int(n_degenerate),
        "watertight": bool(mesh.is_watertight),
        "volume_mm3": float(mesh.volume),
        "bounds_mm": [[round(float(v), 3) for v in row] for row in mesh.bounds.tolist()],
    }
    print(json.dumps(result, indent=2))

    ok = result["watertight"] and result["volume_mm3"] > 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
