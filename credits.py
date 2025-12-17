import json
import os

HISTORY_FILE = "credit_history.json"
LIMIT = 1000  # Parcl Free Tier Limit

def load_usage():
    """Reads current usage from the hidden file."""
    if not os.path.exists(HISTORY_FILE):
        return 0
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("used", 0)
    except:
        return 0

def save_usage(used):
    """Updates the usage file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump({"used": used}, f)

def spend(amount):
    """
    The Gatekeeper.
    1. Checks if (Current + Amount) > Limit.
    2. If YES: Raises an Error (Stopping the app).
    3. If NO: Updates the file and allows the app to proceed.
    """
    current = load_usage()
    
    if current + amount > LIMIT:
        raise Exception(f"⛔ STOP: Credit Limit Reached! ({current}/{LIMIT}). Upgrade or wait for reset.")
    
    # Commit the spend
    save_usage(current + amount)
    return current + amount

def get_status():
    """Returns (Used, Limit) for the Dashboard UI."""
    return load_usage(), LIMIT

def reset():
    """Resets counter to 0 (Use this when your billing month restarts)."""
    save_usage(0)
