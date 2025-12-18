import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class LogLevel(Enum):
    VERBOSE = 'V'
    DEBUG = 'D'
    INFO = 'I'
    WARNING = 'W'
    ERROR = 'E'
    FATAL = 'F'

@dataclass
class LogEntry:
    timestamp: datetime
    process_id: int
    thread_id: int
    level: LogLevel
    tag: str
    message: str
    raw_line: str

class LogParser:
    def __init__(self):
        # Regex pattern for threadtime format: MM-DD HH:MM:SS.mmm PID TID PRIORITY TAG: MESSAGE
        self.pattern = re.compile(
            r'^(\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEFS])\s+([^:]+):\s*(.*)$'
        )
        self.current_year = datetime.now().year

    def parse_batch(self, lines: List[str]) -> List[LogEntry]:
        """Parse a batch of log lines into LogEntry objects"""
        entries = []
        last_entry = None

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            match = self.pattern.match(line)
            if match:
                # Parse new entry
                entry = self._parse_line(match)
                if entry:
                    entries.append(entry)
                    last_entry = entry
            else:
                # Continuation line or malformed line
                if last_entry:
                    # Append to previous entry's message
                    last_entry.message += '\n' + line
                    last_entry.raw_line += '\n' + line
                else:
                    # Malformed line - create entry with current timestamp
                    entry = LogEntry(
                        timestamp=datetime.now(),
                        process_id=0,
                        thread_id=0,
                        level=LogLevel.INFO,
                        tag="UNKNOWN",
                        message=line,
                        raw_line=line
                    )
                    entries.append(entry)
                    last_entry = entry

        return entries

    def _parse_line(self, match) -> Optional[LogEntry]:
        """Parse a single matched log line"""
        try:
            month_day, time_str, pid_str, tid_str, level_char, tag, message = match.groups()

            # Parse timestamp
            month, day = map(int, month_day.split('-'))
            hour, minute, second_milli = time_str.split(':')
            second, milli = second_milli.split('.')
            hour, minute, second, milli = map(int, [hour, minute, second, milli])

            timestamp = datetime(
                self.current_year, month, day, hour, minute, second, milli * 1000
            )

            # Adjust year if timestamp is in future (log from previous year)
            if timestamp > datetime.now():
                timestamp = timestamp.replace(year=self.current_year - 1)

            # Parse other fields
            process_id = int(pid_str)
            thread_id = int(tid_str)
            level = LogLevel(level_char)

            return LogEntry(
                timestamp=timestamp,
                process_id=process_id,
                thread_id=thread_id,
                level=level,
                tag=tag.strip(),
                message=message,
                raw_line=match.string
            )
        except (ValueError, KeyError) as e:
            print(f"Error parsing log line: {e}")
            return None
