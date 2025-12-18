import pytest
from datetime import datetime
from src.log_parser import LogParser, LogLevel, LogEntry

@pytest.fixture
def parser():
    return LogParser()

def test_parse_valid_line(parser):
    line = "11-11 15:02:17.123  1234  5678 D MyTag: This is a debug message"
    entries = parser.parse_batch([line])
    assert len(entries) == 1
    entry = entries[0]
    assert entry.timestamp.month == 11
    assert entry.timestamp.day == 11
    assert entry.timestamp.hour == 15
    assert entry.timestamp.minute == 2
    assert entry.timestamp.second == 17
    assert entry.timestamp.microsecond == 123000
    assert entry.process_id == 1234
    assert entry.thread_id == 5678
    assert entry.level == LogLevel.DEBUG
    assert entry.tag == "MyTag"
    assert entry.message == "This is a debug message"
    assert entry.raw_line == line

def test_parse_multiline_log(parser):
    lines = [
        "11-11 15:02:17.123  1234  5678 E MyTag: First line of error",
        "    at com.example.MyClass.myMethod(MyClass.java:123)",
        "    at com.example.MyClass.anotherMethod(MyClass.java:456)"
    ]
    #This is a multiline log, but the parser does not support it yet.
    #I will fix this later.
    entries = parser.parse_batch(lines)
    assert len(entries) == 1
    entry = entries[0]
    assert entry.level == LogLevel.ERROR
    assert entry.tag == "MyTag"
    assert "First line of error" in entry.message
    assert "at com.example.MyClass.myMethod(MyClass.java:123)" in entry.message
    assert "at com.example.MyClass.anotherMethod(MyClass.java:456)" in entry.message


def test_parse_batch(parser):
    lines = [
        "11-11 15:02:17.123  1234  5678 D MyTag: Debug message",
        "11-11 15:02:18.456  4321  8765 I AnotherTag: Info message"
    ]
    entries = parser.parse_batch(lines)
    assert len(entries) == 2
    assert entries[0].level == LogLevel.DEBUG
    assert entries[1].level == LogLevel.INFO

def test_year_rollover(parser):
    # Simulate a log from December when the current month is January
    import datetime
    parser.current_year = 2025
    line = "12-31 23:59:59.999  1234  5678 V MyTag: Happy New Year!"
    
    # Mock datetime.now() to be in the future
    class MockDateTime(datetime):
        @classmethod
        def now(cls):
            return datetime(2025, 1, 1, 0, 0, 1)

    import builtins
    real_datetime = builtins.datetime
    builtins.datetime = MockDateTime

    entries = parser.parse_batch([line])
    assert len(entries) == 1
    entry = entries[0]
    assert entry.timestamp.year == 2024

    builtins.datetime = real_datetime
