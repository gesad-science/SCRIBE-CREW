from fastapi import FastAPI, UploadFile, File, Form
from pathlib import Path
import shutil
import uvicorn
from tests.run_execution import run_execution
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.agents.core_agent.core_agent import CoreAgent

from pydantic import BaseModel

import os
from dotenv import load_dotenv

load_dotenv()
import builtins
import sys
#builtins.input = lambda *args, **kwargs: "n"
#sys.stdin = open("/dev/null")
#os.close(0)
os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY")


class ExecuteRequest(BaseModel):
    message: str

app = FastAPI()
core = CoreAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["*"] para dev
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDF_DIR = Path("pdfs")
PDF_DIR.mkdir(exist_ok=True)

@app.post("/execute")
def execute(req: ExecuteRequest):
    return run_execution(core=core, user_input=req.message)


@app.post("/execute-with-pdf")
async def execute_with_pdf(
    user_input: str = Form(...),
    pdf: UploadFile = File(...)
):
    file_path = PDF_DIR / pdf.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(pdf.file, buffer)

    user_input = user_input + f" ARTICLE PATH: {file_path}"

    result = run_execution(
        core=core,
        user_input=user_input,
    )

    return {
        "message": "PDF saved",
        "pdf_path": str(file_path),
        "result": result
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
