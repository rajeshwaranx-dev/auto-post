from .files_db import ensure_indexes as _fi
from .users_db import ensure_indexes as _ui

async def init_db():
    await _fi()
    await _ui()
