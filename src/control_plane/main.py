from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from src.control_plane.control_plane import ControlPlane

app = FastAPI()

class CallRequest(BaseModel):
    agent_name: str
    input_data: dict | str


cp = ControlPlane()


@app.get("/agents")
def list_agents():
    return {
        "agents": cp.get_alive_agents()
    }


@app.post("/call")
def call_agent(req: CallRequest):
    try:
        result = cp.call_agent(req.agent_name, req.input_data)
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/refresh")
def refresh():
    cp.discover_agents()
    return {"status": "rescanned"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)
