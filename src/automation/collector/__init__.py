import os
from datetime import timedelta

EPISODE_LENGTH = int(os.getenv("MODULE_EPISODE_LENGTH", 600))
EPISODE_DELTA = timedelta(seconds=EPISODE_LENGTH)
