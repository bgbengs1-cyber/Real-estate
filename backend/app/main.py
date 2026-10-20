"""Application entrypoint (scaffold).

Wire routers, middleware, and lifespan once toolchain and ADRs are approved.
Do not expose unverified production configuration here.
"""

# from fastapi import FastAPI
#
# app = FastAPI(
#     title="PrimeHomes Lead Bot API",
#     version="0.1.0",
#     docs_url="/docs",
#     redoc_url="/redoc",
# )
#
# @app.get("/health")
# async def health() -> dict[str, str]:
#     return {"status": "ok"}
