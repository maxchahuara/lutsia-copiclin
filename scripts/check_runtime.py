#!/usr/bin/env python3
from app.services.runtime_checks import check_capabilities, required_runtime_ok

if __name__ == "__main__":
    for cap in check_capabilities():
        status = "OK" if cap.ok else "MISSING"
        hint = f" | {cap.install_hint}" if cap.install_hint and not cap.ok else ""
        print(f"{status:7} {cap.id:16} {cap.required_for} :: {cap.detail}{hint}")
    raise SystemExit(0 if required_runtime_ok() else 1)
