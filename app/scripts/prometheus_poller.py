#!/usr/bin/env python3
import os
import time
import requests
import sys
from terraform_scale import run_terraform_scale_up
PROM_URL=os.getenv("PROM_URL" , "http://localhost:9090")
INTERVAL=int(os.getenv("INTERVAL", 3))
CPU_THRESHOLD=float(os.getenv("CPU_THRESHOLD_PCT","90.0"))
MEM_THRESHOLD=float(os.getenv("MEM_THRESHOLD_PCT","90.0"))

QUERY_ENDPOINT=f"{PROM_URL.rstrip('/')}/api/v1/query"

QUERIES={
    "cpu_usage_pct": '100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
    "memory_usage_pct": '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
}
def query_prometheus(query: str)-> dict:
    resp=requests.get(QUERY_ENDPOINT , params={"query":query}, timeout=5)
    resp.raise_for_status()
    data=resp.json()
    if data.get("status")!="success":
        raise RuntimeError("prometheus query failed" +str(data))
    return data["data"]
def instant_value_for_query(query:str) -> float:
    d=query_prometheus(query)
    if not d.get("result"):
        return 0.0
    try:
        return float(d["result"][0]["value"][1])
    except Exception:
        return 0.0

def main():
    print(f"starting prometheus poller (interval={INTERVAL}s)...")
    while True:
        try:
            cpu_usage=instant_value_for_query(QUERIES["cpu_usage_pct"])
            mem_usage=instant_value_for_query(QUERIES["memory_usage_pct"])

            ts=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"\n[{ts}] CPU:{cpu_usage:.1f}% | Mem:{mem_usage:.1f}%")
            if cpu_usage >= CPU_THRESHOLD or mem_usage >=MEM_THRESHOLD:
                print(f"⚠ ALERT: High CPU ({cpu_usage:.1f}%) or Memory ({mem_usage:.1f}%) detected!")
                run_terraform_scale_up()

        except Exception as e:
            print("❌ ERROR while polling Prometheus:", e, file=sys.stderr)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()