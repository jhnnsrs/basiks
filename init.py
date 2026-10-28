"""Bake the scikit-image samples Generate Test Image offers into the image, so it works offline.

Only the ones the app offers (`DataKind`), not `data.download_all()`: that fetches every file
scikit-image knows from gitlab.com, which rate-limits a CI runner (429) partway through. Each
sample is retried with a growing pause, since a 429 says to come back later.
"""

import time

from requests.exceptions import HTTPError

from app import DataKind, load_sample


for kind in DataKind:
    for attempt in range(6):
        try:
            load_sample(kind)
            break
        except HTTPError as error:
            if attempt == 5 or error.response is None or error.response.status_code not in (429, 502, 503):
                raise
            time.sleep(10 * 2**attempt)
