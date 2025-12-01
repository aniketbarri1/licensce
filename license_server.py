from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

# Simple in-memory license store
licenses = {}

class ActivateReq(BaseModel):
    key: str
    hwid: str


@app.post("/activate")
def activate(req: ActivateReq):
    key = req.key.strip()
    hwid = req.hwid.strip()

    if key not in licenses:
        return {"status": "invalid"}

    lic = licenses[key]

    if lic["blocked"]:
        return {"status": "blocked"}

    if datetime.utcnow() > lic["expires"]:
        return {"status": "expired"}

    # hwid mismatch
    if lic["hwid"] and lic["hwid"] != hwid:
        return {"status": "hwid_mismatch"}

    # first time bind
    if not lic["hwid"]:
        lic["hwid"] = hwid

    return {"status": "active"}


@app.get("/create/{key}/{days}")
def create(key: str, days: int):
    """New license with validity"""
    expires = datetime.utcnow() + timedelta(days=days)
    licenses[key] = {
        "expires": expires,
        "hwid": "",
        "blocked": False,
    }
    return {
        "ok": True,
        "action": "create",
        "key": key,
        "expires": str(expires),
    }


@app.get("/reset/{key}")
def reset_hwid(key: str):
    """Reset device (HWID) for this key"""
    if key not in licenses:
        return {"ok": False, "error": "not_found"}
    licenses[key]["hwid"] = ""
    return {"ok": True, "action": "reset_hwid", "key": key}


@app.get("/extend/{key}/{days}")
def extend(key: str, days: int):
    """Set / change validity (days from now)"""
    if key not in licenses:
        return {"ok": False, "error": "not_found"}
    new_exp = datetime.utcnow() + timedelta(days=days)
    licenses[key]["expires"] = new_exp
    return {
        "ok": True,
        "action": "extend",
        "key": key,
        "new_expires": str(new_exp),
    }


@app.get("/block/{key}")
def block(key: str):
    """Block license completely"""
    if key not in licenses:
        return {"ok": False, "error": "not_found"}
    licenses[key]["blocked"] = True
    return {"ok": True, "action": "block", "key": key}


@app.get("/info/{key}")
def info(key: str):
    if key not in licenses:
        return {"ok": False, "error": "not_found"}
    lic = licenses[key]
    return {
        "ok": True,
        "key": key,
        "expires": str(lic["expires"]),
        "hwid": lic["hwid"],
        "blocked": lic["blocked"],
    }


@app.get("/list")
def list_all():
    data = []
    for k, v in licenses.items():
        data.append({
            "key": k,
            "expires": str(v["expires"]),
            "hwid": v["hwid"],
            "blocked": v["blocked"],
        })
    return {"ok": True, "licenses": data}
