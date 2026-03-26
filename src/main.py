import asyncio
import os
import sys

import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.DefaultEventLoopPolicy()
        if not hasattr(asyncio, "WindowsSelectorEventLoopPolicy")
        else asyncio.WindowsSelectorEventLoopPolicy()
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "src.api.rest.app:app",
        host=host,
        port=port,
        reload=True,
        loop="asyncio",
    )
