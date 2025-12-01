from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

licenses = {}   # In-memory – sirf server par rahega

class Req(BaseModel):
    key: str
    hwid: str

class CreateReq(BaseModel):
    key: str
    days: int  # kitne din valid

@app.post("/activate")
def activate(req: Req):
    key = req.key.strip()
    hwid = req.hwid.strip()

    if key not in licenses:
        return {"status": "invalid"}

    lic = licenses[key]

    if lic["blocked"]:
        return {"status": "blocked"}

    if datetime.utcnow() > lic["expires"]:
        return {"status": "expired"}

    if lic["hwid"] != "" and lic["hwid"] != hwid:
        return {"status": "hwid_mismatch"}

    if lic["hwid"] == "":
        lic["hwid"] = hwid

    return {"status": "active"}

@app.post("/admin/create")
def create(req: CreateReq):
    key = req.key.strip()
    expires = datetime.utcnow() + timedelta(days=req.days)
    licenses[key] = {
        "expires": expires,
        "hwid": "",
        "blocked": False
    }
    return {"created": True, "key": key, "expires": str(expires)}

@app.get("/admin/block/{key}")
def block(key: str):
    if key in licenses:
        licenses[key]["blocked"] = True
        return {"status": "blocked"}
    return {"error": "not_found"}

@app.get("/admin/info/{key}")
def info(key: str):
    if key in licenses:
        d = licenses[key].copy()
        d["expires"] = str(d["expires"])
        return d
    return {"error": "not_found"}
