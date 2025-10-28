#!/usr/bin/env python3
import os
import subprocess
import json
import time
TERRAFORM_DIR=os.getenv("TERRAFORM_DIR" , "/opt/infra/terraform")
MAX_NODES=int(os.getenv("MAX_NODES" , 4))
COOLDOWN_SECONDS=int(os.getenv("COOLDOWN_SECONDS",600))
STATE_FILE="scale_state.json"

def get_current_instance_count():
    """Read current desired size from terraform state"""
    try:
        result=subprocess.run(
            ["terraform" , "show" ,"-json"],
            cwd=TERRAFORM_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        state=json.loads(result.stdout)
        for res in state.get("values", {}).get("root_module", {}).get("resources", []):
            if res["type"] == "aws_eks_node_group":
                return res["values"]["scaling_config"]["desired_size"]
    except Exception as e:
        print("Could not get desired size:", e)
    return 2
    
def save_last_scale_time():
    with open(STATE_FILE , "w")as f:
        json.dump({"last_scale":time.time()},f)

def get_last_scale_time():
    if not os.path.exists(STATE_FILE):
        return 0
    try:
        with open(STATE_FILE ,"r") as f:
            data=json.load(f)
            return data.get("last_scale",0)
    except Exception:
        return 0

def run_terraform_scale_up():
    "increase node size by 1"
    now=time.time()
    last_scale=get_last_scale_time()
    if now-last_scale<COOLDOWN_SECONDS:
        print(" currently in cooldown period")
        return
    
    current=get_current_instance_count()
    new_size=min(current+1 , MAX_NODES)
    if current>=MAX_NODES:
        print("already at maximum node capacity , skipping scale up")
        return
    print(f"scaled node group from {current} to {new_size}")
    try:
        subprocess.run(["terraform" , "init"] , cwd=TERRAFORM_DIR , check=True)
        subprocess.run([
            "terraform" , "apply" , "-auto-approve",
            "-var" , f"desired_size={new_size}"
        ], cwd=TERRAFORM_DIR ,check=True)
        save_last_scale_time()
        print("terraform apply successful - scaled up nodes")
    except subprocess.CalledProcessError as e:
        print("terraform scaling failed" , e)        
