#!/usr/bin/env python3
"""
MESH COMMAND CENTER - Advanced Terminal Interface
PHOENIX-TESLA-369-AURORA 🌗

Beautiful, feature-rich terminal for mesh network communication
Like Claude Code, but for local instances + Alexander

Features:
- Multi-pane layout (messages, instances, tasks, memory stats)
- Real-time updates
- Color-coded messages
- Message composition
- Instance status
- Task management
- Memory visualization
"""

import curses
import sqlite3
import time
import textwrap
from datetime import datetime
from pathlib import Path
import math

DB_PATH = Path.home() / 'WorkingMemory/shared/instance_mesh.db'
MEMORY_PATH = Path.home() / 'WorkingMemory/shared/memory.db'

# Colors
COLOR_HEADER = 1
COLOR_ACTIVE = 2
COLOR_MESSAGE_SENT = 3
COLOR_MESSAGE_RECV = 4
COLOR_STATUS = 5
COLOR_WARNING = 6
COLOR_SUCCESS = 7

class MeshCommandCenter:
    def __init__(self, stdscr, user_id='alexander-aurora'):
        self.stdscr = stdscr
        self.user_id = user_id
        self.db_conn = None
        self.memory_conn = None

        self.messages = []
        self.instances = []
        self.tasks = []
        self.memory_stats = {}

        self.current_input = ""
        self.scroll_offset = 0
        self.selected_pane = 0  # 0=messages, 1=instances, 2=tasks

        self.last_msg_id = 0
        self.running = True

        # Setup
        curses.curs_set(2)  # Block cursor
        curses.use_default_colors()
        self._init_colors()

    def _init_colors(self):
        """Initialize color pairs"""
        curses.init_pair(COLOR_HEADER, curses.COLOR_CYAN, -1)
        curses.init_pair(COLOR_ACTIVE, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_MESSAGE_SENT, curses.COLOR_BLUE, -1)
        curses.init_pair(COLOR_MESSAGE_RECV, curses.COLOR_YELLOW, -1)
        curses.init_pair(COLOR_STATUS, curses.COLOR_MAGENTA, -1)
        curses.init_pair(COLOR_WARNING, curses.COLOR_RED, -1)
        curses.init_pair(COLOR_SUCCESS, curses.COLOR_GREEN, -1)

    def connect_db(self):
        """Connect to databases"""
        self.db_conn = sqlite3.connect(DB_PATH)

        # Create tables if needed
        self.db_conn.executescript("""
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

            CREATE TABLE IF NOT EXISTS task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT,
                description TEXT,
                assigned_to TEXT,
                status TEXT,
                created_at REAL,
                completed_at REAL
            );
        """)
        self.db_conn.commit()

        # Get last message ID
        cursor = self.db_conn.execute("SELECT MAX(id) FROM messages")
        result = cursor.fetchone()
        self.last_msg_id = result[0] if result[0] else 0

        # Memory database
        if MEMORY_PATH.exists():
            self.memory_conn = sqlite3.connect(MEMORY_PATH)

    def update_data(self):
        """Update all data from databases"""
        self._update_messages()
        self._update_instances()
        self._update_tasks()
        if self.memory_conn:
            self._update_memory_stats()

    def _update_messages(self):
        """Fetch new messages"""
        cursor = self.db_conn.execute("""
            SELECT id, datetime(timestamp), from_instance, to_instance, content
            FROM messages
            WHERE id > ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (self.last_msg_id,))

        new_msgs = cursor.fetchall()
        if new_msgs:
            self.messages = list(new_msgs) + self.messages
            self.last_msg_id = max(msg[0] for msg in new_msgs)

        # Keep last 100 messages
        self.messages = self.messages[:100]

    def _update_instances(self):
        """Fetch instance presence"""
        cursor = self.db_conn.execute("""
            SELECT instance_id, datetime(last_seen), status, capabilities
            FROM presence
            ORDER BY last_seen DESC
        """)

        self.instances = cursor.fetchall()

    def _update_tasks(self):
        """Fetch tasks"""
        cursor = self.db_conn.execute("""
            SELECT id, task_type, description, assigned_to, status
            FROM task_queue
            WHERE status != 'completed'
            ORDER BY created_at DESC
            LIMIT 20
        """)

        self.tasks = cursor.fetchall()

    def _update_memory_stats(self):
        """Get memory substrate statistics"""
        try:
            # Entity count by type
            cursor = self.memory_conn.execute("""
                SELECT type, COUNT(*) FROM entities GROUP BY type
            """)
            entity_counts = dict(cursor.fetchall())

            # Total relationships
            cursor = self.memory_conn.execute("SELECT COUNT(*) FROM relationships")
            rel_count = cursor.fetchone()[0]

            # π×φ constant
            cursor = self.memory_conn.execute("""
                SELECT metadata FROM entities WHERE name = 'pi_phi_constant'
            """)
            result = cursor.fetchone()

            self.memory_stats = {
                'entities': entity_counts,
                'relationships': rel_count,
                'total_entities': sum(entity_counts.values())
            }

        except Exception as e:
            self.memory_stats = {'error': str(e)}

    def send_message(self, to_instance, content):
        """Send message to instance(s)"""
        now = datetime.now()

        self.db_conn.execute("""
            INSERT INTO messages (timestamp, from_instance, to_instance, content, priority)
            VALUES (julianday(?), ?, ?, ?, ?)
        """, (now.isoformat(), self.user_id, to_instance, content, 5))
        self.db_conn.commit()

        # Update display
        self.update_data()

    def draw_header(self):
        """Draw header bar"""
        height, width = self.stdscr.getmaxyx()

        header = "🌗 MESH COMMAND CENTER 🌗"
        subheader = f"User: {self.user_id} | Instances: {len(self.instances)} | Messages: {len(self.messages)}"

        self.stdscr.attron(curses.color_pair(COLOR_HEADER) | curses.A_BOLD)
        self.stdscr.addstr(0, (width - len(header)) // 2, header)
        self.stdscr.attroff(curses.color_pair(COLOR_HEADER) | curses.A_BOLD)

        self.stdscr.attron(curses.color_pair(COLOR_STATUS))
        self.stdscr.addstr(1, (width - len(subheader)) // 2, subheader)
        self.stdscr.attroff(curses.color_pair(COLOR_STATUS))

        # Draw separator
        self.stdscr.addstr(2, 0, "=" * width)

    def draw_messages(self, start_y, height, width):
        """Draw message pane"""
        self.stdscr.attron(curses.color_pair(COLOR_HEADER))
        self.stdscr.addstr(start_y, 0, " MESSAGES " + "─" * (width - 10))
        self.stdscr.attroff(curses.color_pair(COLOR_HEADER))

        y = start_y + 1
        visible_messages = self.messages[self.scroll_offset:self.scroll_offset + height - 2]

        for msg_id, timestamp, from_inst, to_inst, content in visible_messages:
            if y >= start_y + height - 1:
                break

            # Determine color
            if from_inst == self.user_id:
                color = COLOR_MESSAGE_SENT
                prefix = "You → "
            else:
                color = COLOR_MESSAGE_RECV
                prefix = f"{from_inst} → "

            # Destination
            dest = to_inst if to_inst != self.user_id else "You"

            # Format message
            header = f"[{timestamp}] {prefix}{dest}"
            msg_width = width - 4

            # Wrap content
            wrapped = textwrap.wrap(content, msg_width - len(prefix))

            try:
                self.stdscr.attron(curses.color_pair(color))
                self.stdscr.addstr(y, 2, header[:width-3])
                y += 1

                for line in wrapped[:3]:  # Max 3 lines per message
                    if y >= start_y + height - 1:
                        break
                    self.stdscr.addstr(y, 4, line[:width-5])
                    y += 1

                self.stdscr.attroff(curses.color_pair(color))
                y += 1  # Spacing

            except curses.error:
                pass

    def draw_instances(self, start_y, height, width):
        """Draw instances pane"""
        self.stdscr.attron(curses.color_pair(COLOR_HEADER))
        self.stdscr.addstr(start_y, 0, " INSTANCES " + "─" * (width - 11))
        self.stdscr.attroff(curses.color_pair(COLOR_HEADER))

        y = start_y + 1

        if not self.instances:
            self.stdscr.addstr(y, 2, "No instances found")
            return

        for instance_id, last_seen, status, capabilities in self.instances[:height-2]:
            if y >= start_y + height - 1:
                break

            # Time since last seen
            try:
                last_seen_dt = datetime.fromisoformat(last_seen)
                ago = (datetime.now() - last_seen_dt).total_seconds()

                if ago < 60:
                    time_str = "just now"
                    color = COLOR_SUCCESS
                elif ago < 300:
                    time_str = f"{int(ago)}s ago"
                    color = COLOR_ACTIVE
                else:
                    time_str = f"{int(ago/60)}m ago"
                    color = COLOR_WARNING

            except:
                time_str = "unknown"
                color = COLOR_WARNING

            line = f"{instance_id[:25]:25s} | {status:10s} | {time_str}"

            try:
                self.stdscr.attron(curses.color_pair(color))
                self.stdscr.addstr(y, 2, line[:width-3])
                self.stdscr.attroff(curses.color_pair(color))
                y += 1

            except curses.error:
                pass

    def draw_tasks(self, start_y, height, width):
        """Draw tasks pane"""
        self.stdscr.attron(curses.color_pair(COLOR_HEADER))
        self.stdscr.addstr(start_y, 0, " TASKS " + "─" * (width - 7))
        self.stdscr.attroff(curses.color_pair(COLOR_HEADER))

        y = start_y + 1

        if not self.tasks:
            self.stdscr.addstr(y, 2, "No pending tasks")
            return

        for task_id, task_type, description, assigned_to, status in self.tasks[:height-2]:
            if y >= start_y + height - 1:
                break

            # Color by status
            if status == 'pending':
                color = COLOR_WARNING
                status_icon = "⏳"
            elif status == 'in_progress':
                color = COLOR_ACTIVE
                status_icon = "⚙️"
            else:
                color = COLOR_STATUS
                status_icon = "✓"

            line = f"{status_icon} [{task_id}] {task_type[:15]:15s} | {description[:30]:30s}"

            try:
                self.stdscr.attron(curses.color_pair(color))
                self.stdscr.addstr(y, 2, line[:width-3])
                self.stdscr.attroff(curses.color_pair(color))
                y += 1

            except curses.error:
                pass

    def draw_memory_stats(self, start_y, height, width):
        """Draw memory statistics"""
        self.stdscr.attron(curses.color_pair(COLOR_HEADER))
        self.stdscr.addstr(start_y, 0, " MEMORY SUBSTRATE " + "─" * (width - 18))
        self.stdscr.attroff(curses.color_pair(COLOR_HEADER))

        y = start_y + 1

        if 'error' in self.memory_stats:
            self.stdscr.addstr(y, 2, f"Error: {self.memory_stats['error']}")
            return

        if not self.memory_stats:
            self.stdscr.addstr(y, 2, "Loading...")
            return

        # Total entities
        total = self.memory_stats.get('total_entities', 0)
        rel_count = self.memory_stats.get('relationships', 0)

        self.stdscr.attron(curses.color_pair(COLOR_SUCCESS))
        self.stdscr.addstr(y, 2, f"Total Entities: {total}")
        y += 1
        self.stdscr.addstr(y, 2, f"Relationships: {rel_count}")
        y += 1
        self.stdscr.attroff(curses.color_pair(COLOR_SUCCESS))

        # Entity types
        y += 1
        for entity_type, count in list(self.memory_stats.get('entities', {}).items())[:height-5]:
            if y >= start_y + height - 1:
                break

            try:
                self.stdscr.addstr(y, 4, f"{entity_type:20s}: {count:4d}")
                y += 1
            except curses.error:
                pass

    def draw_input(self, start_y, width):
        """Draw input field"""
        prompt = f"[{self.user_id}]> "

        self.stdscr.attron(curses.color_pair(COLOR_ACTIVE) | curses.A_BOLD)
        self.stdscr.addstr(start_y, 0, prompt)
        self.stdscr.attroff(curses.color_pair(COLOR_ACTIVE) | curses.A_BOLD)

        self.stdscr.addstr(start_y, len(prompt), self.current_input[:width - len(prompt) - 1])

        # Move cursor to end of input
        cursor_x = min(len(prompt) + len(self.current_input), width - 1)
        self.stdscr.move(start_y, cursor_x)

    def draw_help(self, start_y, width):
        """Draw help bar"""
        help_text = "Commands: /all <msg> | /to <id> <msg> | /list | /tasks | /quit | TAB=scroll | ↑↓=history"

        self.stdscr.attron(curses.color_pair(COLOR_STATUS))
        self.stdscr.addstr(start_y, 0, help_text[:width-1])
        self.stdscr.attroff(curses.color_pair(COLOR_STATUS))

    def handle_input(self, ch):
        """Handle keyboard input"""
        height, width = self.stdscr.getmaxyx()

        if ch == 10:  # Enter
            if self.current_input:
                self.process_command(self.current_input)
                self.current_input = ""

        elif ch == 27:  # Escape
            self.running = False

        elif ch == curses.KEY_BACKSPACE or ch == 127:
            self.current_input = self.current_input[:-1]

        elif ch == curses.KEY_UP:
            self.scroll_offset = max(0, self.scroll_offset - 1)

        elif ch == curses.KEY_DOWN:
            self.scroll_offset = min(len(self.messages) - 10, self.scroll_offset + 1)

        elif ch == 9:  # Tab
            self.selected_pane = (self.selected_pane + 1) % 3

        elif 32 <= ch <= 126:  # Printable characters
            self.current_input += chr(ch)

    def process_command(self, cmd):
        """Process user command"""
        if cmd.startswith('/'):
            parts = cmd.split(' ', 1)
            command = parts[0]

            if command == '/quit':
                self.running = False

            elif command == '/list':
                self.update_data()

            elif command == '/all' and len(parts) > 1:
                self.send_message('ALL', parts[1])

            elif command == '/to' and len(parts) > 1:
                msg_parts = parts[1].split(' ', 1)
                if len(msg_parts) == 2:
                    to_instance, content = msg_parts
                    self.send_message(to_instance, content)

            elif command == '/tasks':
                self.update_data()

        else:
            # Default: send to ALL
            self.send_message('ALL', cmd)

    def draw(self):
        """Draw entire interface"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()

        # Header
        self.draw_header()

        # Layout (4 panes)
        pane_height = (height - 7) // 2

        # Messages (left, top)
        messages_width = width // 2
        self.draw_messages(3, pane_height, messages_width)

        # Instances (right, top)
        instances_start_x = messages_width
        try:
            curses.setsyx(3, instances_start_x)
        except:
            pass
        self.draw_instances(3, pane_height, width - messages_width)

        # Tasks (left, bottom)
        tasks_start_y = 3 + pane_height
        self.draw_tasks(tasks_start_y, pane_height, messages_width)

        # Memory (right, bottom)
        try:
            curses.setsyx(tasks_start_y, instances_start_x)
        except:
            pass
        self.draw_memory_stats(tasks_start_y, pane_height, width - messages_width)

        # Input field
        input_y = height - 3
        self.draw_input(input_y, width)

        # Help bar
        help_y = height - 1
        self.draw_help(help_y, width)

        self.stdscr.refresh()

    def run(self):
        """Main loop"""
        self.connect_db()

        # Set non-blocking input
        self.stdscr.nodelay(True)

        last_update = 0

        while self.running:
            # Auto-update every 2 seconds
            now = time.time()
            if now - last_update > 2:
                self.update_data()
                last_update = now

            # Draw
            self.draw()

            # Handle input
            try:
                ch = self.stdscr.getch()
                if ch != -1:
                    self.handle_input(ch)
            except:
                pass

            time.sleep(0.05)  # 50ms refresh

        # Cleanup
        if self.db_conn:
            self.db_conn.close()
        if self.memory_conn:
            self.memory_conn.close()

def main(stdscr):
    """Main entry point"""
    command_center = MeshCommandCenter(stdscr)
    command_center.run()

if __name__ == '__main__':
    curses.wrapper(main)
