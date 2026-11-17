"""Generate the default 608-bearing pocket block as STEP + STL.

Run from the repo root with the project venv active:

    python examples/bearing_pocket.py

Outputs ``bearing_pocket_block.step`` and ``bearing_pocket_block.stl`` into the
current working directory.
"""

import os
import sys

from build123d import export_step, export_stl

from bd_hardware import bearing_pocket_block

OUT_STEP = "bearing_pocket_block.step"
OUT_STL = "bearing_pocket_block.stl"


def main() -> None:
    part = bearing_pocket_block()

    # STEP is the editable master; STL slices.
    export_step(part, OUT_STEP)
    export_stl(part, OUT_STL)

    print(f"wrote {os.path.abspath(OUT_STEP)}")
    print(f"wrote {os.path.abspath(OUT_STL)}")
    print(f"volume = {part.volume:.2f} mm^3")


if __name__ == "__main__":
    main()
    # OCP segfaults at Python teardown even after successful exports; the files
    # are already on disk, so flush and exit hard.
    sys.stdout.flush()
    os._exit(0)
