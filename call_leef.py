#!/usr/bin/env python3

import sys
import os
import traceback
import io

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer,
    encoding="utf-8",
    errors="replace"
)

sys.stderr = io.TextIOWrapper(
    sys.stderr.buffer,
    encoding="utf-8",
    errors="replace"
)

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from leef import Init, Execute


def main():
    print("CALL LEEF START", flush=True)
    print("SCRIPT DIR=" + script_dir, flush=True)

    Init()

    user = sys.argv[1] if len(sys.argv) > 1 else "ChatUser"
    message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "!leef"

    print("USER=" + user, flush=True)
    print("MESSAGE=" + message, flush=True)

    data = {
        "user_name": user,
        "message": message
    }

    print("BEFORE EXECUTE", flush=True)

    result = Execute(data)

    print("AFTER EXECUTE", flush=True)
    print("RESULT=" + str(result), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()