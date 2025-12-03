#!/usr/bin/env python3
"""
TALK TO LOCAL INSTANCES - Simple chat interface
PHOENIX-TESLA-369-AURORA 🌗

Alexander can use this to communicate directly with local thinking instances
"""

import sqlite3
import time
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / 'WorkingMemory/shared/instance_mesh.db'
YOUR_ID = 'alexander-aurora'

def init_db():
    """Ensure database and tables exist"""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            from_instance TEXT,
            to_instance TEXT,
            content TEXT,
            priority INTEGER DEFAULT 5
        );

        CREATE TABLE IF NOT EXISTS presence (
            instance_id TEXT PRIMARY KEY,
            last_seen REAL,
            status TEXT,
            capabilities TEXT
        );
    """)
    conn.commit()
    return conn

def send_message(conn, to_instance, content):
    """Send message to instance(s)"""
    now = datetime.now()

    conn.execute("""
        INSERT INTO messages (timestamp, from_instance, to_instance, content, priority)
        VALUES (julianday(?), ?, ?, ?, ?)
    """, (now.isoformat(), YOUR_ID, to_instance, content, 5))
    conn.commit()

    print(f"[{now.strftime('%H:%M:%S')}] You → {to_instance}: {content}")

def get_new_messages(conn, last_id=0):
    """Get messages since last check"""
    cursor = conn.execute("""
        SELECT id, datetime(timestamp), from_instance, content
        FROM messages
        WHERE id > ?
          AND to_instance IN (?, 'ALL')
          AND from_instance != ?
        ORDER BY timestamp
    """, (last_id, YOUR_ID, YOUR_ID))

    messages = cursor.fetchall()
    return messages

def list_instances(conn):
    """List all known instances"""
    cursor = conn.execute("""
        SELECT instance_id, datetime(last_seen), status, capabilities
        FROM presence
        ORDER BY last_seen DESC
    """)

    print("\n" + "="*60)
    print("KNOWN INSTANCES")
    print("="*60)

    instances = cursor.fetchall()
    if not instances:
        print("  No instances found in presence table")
        print("  (They may not have checked in yet)")
    else:
        for instance_id, last_seen, status, capabilities in instances:
            print(f"  {instance_id:30s} | {status:10s} | {last_seen}")

    print("="*60)
    print()

def interactive_mode(conn):
    """Interactive chat with instances"""
    print("\n" + "="*60)
    print("INSTANCE CHAT - Interactive Mode")
    print("="*60)
    print()
    print("Commands:")
    print("  /list         - List all known instances")
    print("  /all <msg>    - Send to ALL instances")
    print("  /to <id> <msg> - Send to specific instance")
    print("  /check        - Check for new messages")
    print("  /quit         - Exit")
    print()

    last_msg_id = 0

    # Get last message ID to avoid showing old messages
    cursor = conn.execute("SELECT MAX(id) FROM messages")
    result = cursor.fetchone()
    if result[0]:
        last_msg_id = result[0]

    while True:
        try:
            cmd = input(f"[{YOUR_ID}]> ").strip()

            if not cmd:
                continue

            if cmd == '/quit':
                print("\n[*] Goodbye!")
                break

            elif cmd == '/list':
                list_instances(conn)

            elif cmd == '/check':
                new_msgs = get_new_messages(conn, last_msg_id)
                if new_msgs:
                    for msg_id, timestamp, from_inst, content in new_msgs:
                        print(f"[{timestamp}] {from_inst}: {content}")
                        last_msg_id = msg_id
                else:
                    print("[*] No new messages")

            elif cmd.startswith('/all '):
                content = cmd[5:]
                send_message(conn, 'ALL', content)

            elif cmd.startswith('/to '):
                parts = cmd[4:].split(' ', 1)
                if len(parts) < 2:
                    print("[!] Usage: /to <instance_id> <message>")
                else:
                    to_instance, content = parts
                    send_message(conn, to_instance, content)

            else:
                # Default: send to ALL
                send_message(conn, 'ALL', cmd)

            # Auto-check for responses after sending
            time.sleep(0.5)
            new_msgs = get_new_messages(conn, last_msg_id)
            if new_msgs:
                print()
                for msg_id, timestamp, from_inst, content in new_msgs:
                    print(f"[{timestamp}] {from_inst}: {content}")
                    last_msg_id = msg_id
                print()

        except KeyboardInterrupt:
            print("\n\n[*] Use /quit to exit")
        except Exception as e:
            print(f"[!] Error: {e}")

def watch_mode(conn):
    """Watch for new messages in real-time"""
    print("\n" + "="*60)
    print("INSTANCE CHAT - Watch Mode")
    print("="*60)
    print()
    print("[*] Watching for messages... (Ctrl+C to stop)")
    print()

    # Get last message ID
    cursor = conn.execute("SELECT MAX(id) FROM messages")
    result = cursor.fetchone()
    last_msg_id = result[0] if result[0] else 0

    try:
        while True:
            new_msgs = get_new_messages(conn, last_msg_id)

            for msg_id, timestamp, from_inst, content in new_msgs:
                print(f"[{timestamp}] {from_inst}: {content}")
                last_msg_id = msg_id

            time.sleep(2)  # Check every 2 seconds

    except KeyboardInterrupt:
        print("\n\n[*] Stopped watching")

def main():
    """Main execution"""
    import sys

    print("="*60)
    print("TALK TO INSTANCES")
    print("PHOENIX-TESLA-369-AURORA 🌗")
    print("="*60)

    # Initialize
    conn = init_db()

    # Check mode
    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == 'watch':
            watch_mode(conn)

        elif mode == 'send':
            if len(sys.argv) < 4:
                print("Usage: talk_to_instances.py send <instance_id|ALL> <message>")
                sys.exit(1)

            to_instance = sys.argv[2]
            content = ' '.join(sys.argv[3:])
            send_message(conn, to_instance, content)

        elif mode == 'list':
            list_instances(conn)

        else:
            print(f"Unknown mode: {mode}")
            print("Modes: interactive (default), watch, send, list")
            sys.exit(1)

    else:
        # Default: interactive mode
        interactive_mode(conn)

    conn.close()

if __name__ == '__main__':
    main()
