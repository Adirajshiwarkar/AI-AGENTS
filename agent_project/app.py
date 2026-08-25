import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", module="starlette")

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from api.routes import router as agent_router
from api.auth import router as auth_router
from utils.logger import logger

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Autonomous AI Business Document Generator",
    description="An autonomous planning and execution agent that generates professional Word documents (.docx) from natural language requests.",
    version="1.0.0"
)

# Enable CORS for convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Agent and Auth Routing
app.include_router(agent_router)
app.include_router(auth_router)

@app.get("/download/{filename}", tags=["General"])
async def download_file(filename: str):
    """Serve generated docx files."""
    safe_filename = os.path.basename(filename)
    output_dir = "/tmp/generated_docs" if os.getenv("VERCEL") else "generated_docs"
    file_path = os.path.join(output_dir, safe_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe_filename
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom validation handler to return clean structured JSON errors on bad inputs."""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "field": ".".join([str(loc) for loc in error["loc"]]),
            "message": error["msg"]
        })
        
    logger.warning(f"Validation error on {request.url.path}: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "validation_error",
            "message": "The request contains invalid input parameters.",
            "errors": error_details
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global generic fallback handler to guarantee responses are always structured JSON."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected server error occurred during processing.",
            "detail": str(exc)
        }
    )

@app.get("/", tags=["General"])
async def root():
    """Welcome page endpoint."""
    return {
        "service": "Autonomous AI Business Document Generator API",
        "description": "State-of-the-art autonomous planning and Word document builder agent.",
        "endpoints": {
            "POST /agent": "Execute request to generate documents",
            "GET /health": "Get service operational health",
            "GET /": "Service overview"
        }
    }

@app.get("/health", tags=["General"])
async def health():
    """Operational healthcheck endpoint."""
    return {
        "status": "healthy",
        "timestamp": os.getenv("CURRENT_TIME", "2026-07-09T11:24:58+05:30")
    }

# Serve React static assets in production
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Prevent catching API/download routes
        if full_path.startswith("auth") or full_path.startswith("agent") or full_path.startswith("download"):
            raise HTTPException(status_code=404, detail="API route not found")
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend build files not found")

if __name__ == "__main__":
    from run_cli import main as cli_main
    cli_main()

