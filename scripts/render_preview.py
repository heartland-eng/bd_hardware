"""Render a 3D preview of the bearing pocket block to PNG.

Usage: python scripts/render_preview.py <input.stl> <output.png>
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh


def main() -> int:
    stl_path, png_path = sys.argv[1], sys.argv[2]
    mesh = trimesh.load(stl_path)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    verts = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.faces)
    ax.plot_trisurf(
        verts[:, 0],
        verts[:, 1],
        verts[:, 2],
        triangles=faces,
        cmap="viridis",
        edgecolor="none",
        antialiased=True,
    )

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_zlabel("Z (mm)")
    ax.set_title(f"bearing_pocket_block\n{len(faces)} faces, watertight={mesh.is_watertight}")
    ax.view_init(elev=25, azim=-60)

    fig.tight_layout()
    fig.savefig(png_path, dpi=110)
    print(f"wrote {png_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
