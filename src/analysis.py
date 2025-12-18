from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import statistics
from src.log_parser import LogEntry, LogLevel

class LogAnalyzer:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all statistics"""
        self.total_logs = 0
        self.level_counts = {level: 0 for level in LogLevel}
        self.tag_counts = Counter()
        self.process_counts = Counter()
        self.error_messages = Counter()
        self.session_start = datetime.now()
        self.last_update = datetime.now()
        self.logs_per_second = 0.0
        self.peak_logs_per_second = 0.0

    def update_statistics(self, entries: List[LogEntry]):
        """Update statistics with new log entries"""
        if not entries:
            return

        for entry in entries:
            self.total_logs += 1
            self.level_counts[entry.level] += 1
            self.tag_counts[entry.tag] += 1
            self.process_counts[entry.process_id] += 1

            # Track error messages
            if entry.level in [LogLevel.ERROR, LogLevel.FATAL]:
                # Extract first part of message for grouping
                error_key = entry.message.split('\n')[0][:100]  # First 100 chars
                self.error_messages[error_key] += 1

        # Calculate logs per second based on session duration
        session_duration = (datetime.now() - self.session_start).total_seconds()
        if session_duration > 0:
            current_rate = self.total_logs / session_duration
            self.logs_per_second = current_rate
            self.peak_logs_per_second = max(self.peak_logs_per_second, current_rate)

        self.last_update = datetime.now()

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        session_duration = (datetime.now() - self.session_start).total_seconds()

        return {
            'total_logs': self.total_logs,
            'session_duration_seconds': session_duration,
            'logs_per_second_current': self.logs_per_second,
            'logs_per_second_peak': self.peak_logs_per_second,
            'level_breakdown': {level.value: count for level, count in self.level_counts.items()},
            'top_tags': dict(self.tag_counts.most_common(10)),
            'top_processes': dict(self.process_counts.most_common(5)),
            'top_errors': dict(self.error_messages.most_common(5)),
            'error_percentage': (self.level_counts[LogLevel.ERROR] + self.level_counts[LogLevel.FATAL]) / max(self.total_logs, 1) * 100,
            'unique_tags': len(self.tag_counts),
            'unique_processes': len(self.process_counts)
        }

    def detect_anomalies(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect anomalies in log patterns"""
        anomalies = []

        if not entries:
            return anomalies

        # Check for error bursts
        recent_errors = sum(1 for entry in entries[-100:]  # Last 100 entries
                          if entry.level in [LogLevel.ERROR, LogLevel.FATAL])

        if recent_errors > 10:  # Threshold for error burst
            anomalies.append({
                'type': 'error_burst',
                'description': f'High error rate detected: {recent_errors} errors in recent logs',
                'severity': 'high',
                'timestamp': datetime.now()
            })

        # Check for new unknown tags
        new_tags = set(entry.tag for entry in entries)
        known_tags = set(self.tag_counts.keys())

        unknown_tags = new_tags - known_tags
        if unknown_tags:
            anomalies.append({
                'type': 'new_tags',
                'description': f'New tags detected: {", ".join(list(unknown_tags)[:5])}',
                'severity': 'medium',
                'timestamp': datetime.now()
            })

        # Check for process crashes
        crash_indicators = ['FATAL', 'crash', 'exception', 'died']
        crashes = [entry for entry in entries
                  if any(indicator.lower() in entry.message.lower() for indicator in crash_indicators)]

        if crashes:
            anomalies.append({
                'type': 'process_crash',
                'description': f'Potential crash detected in process {crashes[0].process_id}',
                'severity': 'high',
                'timestamp': datetime.now()
            })

        return anomalies

    def get_time_based_stats(self, time_window_minutes: int = 5) -> Dict[str, Any]:
        """Get statistics for recent time window"""
        # Note: This would need historical data to implement properly
        # For now, return current stats
        return self.get_summary_stats()

    def get_tag_categories(self) -> Dict[str, List[str]]:
        """Categorize tags"""
        system_tags = []
        framework_tags = []
        app_tags = []
        custom_tags = []

        for tag in self.tag_counts.keys():
            tag_lower = tag.lower()
            if any(keyword in tag_lower for keyword in ['system', 'android', 'kernel', 'dvm', 'zygote']):
                system_tags.append(tag)
            elif any(keyword in tag_lower for keyword in ['activity', 'window', 'view', 'ui', 'input']):
                framework_tags.append(tag)
            elif '.' in tag or tag.startswith('com.') or tag.startswith('org.'):
                app_tags.append(tag)
            else:
                custom_tags.append(tag)

        return {
            'system': system_tags,
            'framework': framework_tags,
            'application': app_tags,
            'custom': custom_tags
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance-related metrics"""
        return {
            'total_logs_processed': self.total_logs,
            'session_duration_hours': (datetime.now() - self.session_start).total_seconds() / 3600,
            'average_logs_per_second': self.total_logs / max((datetime.now() - self.session_start).total_seconds(), 1),
            'peak_logs_per_second': self.peak_logs_per_second,
            'memory_usage_estimate': self.total_logs * 0.5,  # Rough estimate in KB
            'error_rate': (self.level_counts[LogLevel.ERROR] + self.level_counts[LogLevel.FATAL]) / max(self.total_logs, 1)
        }
