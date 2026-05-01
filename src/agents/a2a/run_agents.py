import uvicorn


from src.agents.a2a.a2a_bibtex import app as bib
from src.agents.a2a.a2a_reference_finder import app as rf
from src.agents.a2a.a2a_rag import app as rag
from src.agents.a2a.a2a_download import app as download
from src.agents.a2a.a2a_validator import app as validator

if __name__ == "__main__":
    uvicorn.run(app=bib, host="0.0.0.0", port=9995)
    uvicorn.run(app=rf, host="0.0.0.0", port=9998)
    uvicorn.run(app=rag, host="0.0.0.0", port=9997)
    uvicorn.run(app=download, host="0.0.0.0", port=9996)
    uvicorn.run(app=validator, host="0.0.0.0", port=9994)
