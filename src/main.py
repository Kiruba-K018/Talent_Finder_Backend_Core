import asyncio
import sys

import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.DefaultEventLoopPolicy()
        if not hasattr(asyncio, "WindowsSelectorEventLoopPolicy")
        else asyncio.WindowsSelectorEventLoopPolicy()
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.api.rest.app:app",
        host="localhost",
        port=8000,
        reload=True,
        loop="asyncio",
    )
