"""The auth provider is chosen at import: the suite runs on the default one (the Life gate).

The default provider (the Life gate) is covered by test_gate.py on its own mini app.
"""

import os

os.environ.setdefault("LIFE_INSTANCE", "")
