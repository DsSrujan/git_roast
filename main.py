import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from analyzer import GitAnalyzer
from roaster import GroqRoaster

app = FastAPI(title="Git-Trace API", description="Sarcastic Git Commit Storyteller")

# Enable CORS so frontend callers can interact without restriction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RoastRequest(BaseModel):
    repo_url: str
    mode: str = "nuclear"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")


@app.get("/")
def serve_ui():
    if os.path.exists(INDEX_PATH):
        return FileResponse(INDEX_PATH)
    return {"status": "online", "message": "Git-Trace API is running hot."}

@app.get("/api/health")
def health_check():
    return {"status": "online", "message": "Git-Trace API is running hot."}

@app.get("/api/modes")
def get_modes():
    return {"modes": list(GroqRoaster.MODES.keys())}

@app.post("/api/roast")
async def generate_roast(req: RoastRequest):
    # 1. Analyze the repository logs
    try:
        analyzer = GitAnalyzer(req.repo_url)
        commits = analyzer.fetch_and_parse(limit=15)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not commits:
        raise HTTPException(status_code=400, detail="Repository log is empty or invalid.")

    # 2. Pass logs to the Groq roaster
    roaster = GroqRoaster()
    story = roaster.roast(commits, mode=req.mode)

    if story.startswith("❌"):
        raise HTTPException(status_code=500, detail=story)

    return {
        "commits_analyzed": len(commits),
        "commits": commits,
        "story": story
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
