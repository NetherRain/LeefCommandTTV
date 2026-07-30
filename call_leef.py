#!/usr/bin/env python3
import sys
from leef import Init, Execute

def main():
    Init()
    user = sys.argv[1] if len(sys.argv) > 1 else "ChatUser"
    # join remaining args as message (so messages with spaces work)
    message = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "!leef"
    data = {"user_name": user, "message": message}
    Execute(data)

if __name__ == "__main__":
    main()
