import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.log_parser import LogEntry
from src.analysis import LogAnalyzer

class LogExporter:
    def __init__(self, config_manager):
        self.config = config_manager

    def export_plain_text(self, entries: List[LogEntry], filepath: str,
                         include_filters: bool = True, filter_description: str = "") -> bool:
        """Export logs as plain text"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"Android Log Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")

                if include_filters and filter_description:
                    f.write(f"Applied Filters: {filter_description}\n\n")

                # Write log entries
                for entry in entries:
                    timestamp_str = entry.timestamp.strftime('%m-%d %H:%M:%S.%f')[:-3]
                    level_str = entry.level.value
                    f.write(f"{timestamp_str} {entry.process_id:5d} {entry.thread_id:5d} {level_str} {entry.tag}: {entry.message}\n")

                # Write summary
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Total entries exported: {len(entries)}\n")

            return True
        except Exception as e:
            print(f"Error exporting to text: {e}")
            return False

    def export_csv(self, entries: List[LogEntry], filepath: str,
                  include_filters: bool = True, filter_description: str = "") -> bool:
        """Export logs as CSV"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(['Timestamp', 'Process_ID', 'Thread_ID', 'Level', 'Tag', 'Message'])

                # Write metadata as comments (CSV doesn't support comments well, so we'll add them as data rows)
                if include_filters and filter_description:
                    writer.writerow(['# Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '', '', '', ''])
                    writer.writerow(['# Applied Filters', filter_description, '', '', '', ''])
                    writer.writerow([])  # Empty row

                # Write log entries
                for entry in entries:
                    timestamp_str = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    writer.writerow([
                        timestamp_str,
                        entry.process_id,
                        entry.thread_id,
                        entry.level.value,
                        entry.tag,
                        entry.message
                    ])

            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False

    def export_json(self, entries: List[LogEntry], filepath: str,
                   include_filters: bool = True, filter_description: str = "") -> bool:
        """Export logs as JSON"""
        try:
            data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_entries': len(entries),
                    'filters_applied': filter_description if include_filters else None
                },
                'logs': []
            }

            for entry in entries:
                log_data = {
                    'timestamp': entry.timestamp.isoformat(),
                    'process_id': entry.process_id,
                    'thread_id': entry.thread_id,
                    'level': entry.level.value,
                    'tag': entry.tag,
                    'message': entry.message,
                    'raw_line': entry.raw_line
                }
                data['logs'].append(log_data)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False

    def export_html(self, entries: List[LogEntry], filepath: str,
                   analyzer: Optional[LogAnalyzer] = None,
                   include_filters: bool = True, filter_description: str = "") -> bool:
        """Export logs as HTML with syntax highlighting"""
        try:
            color_map = self.config.get('color_scheme', {
                'verbose': '#666666',
                'debug': '#ADD8E6',
                'info': '#FFFFFF',
                'warning': '#FFA500',
                'error': '#FF0000',
                'fatal': '#8B0000'
            })

            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android Log Export</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            font-size: {self.config.get('font_size', 10)}px;
            background-color: #1e1e1e;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .log-entry {{
            margin: 2px 0;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .log-timestamp {{ color: #888888; }}
        .log-pid {{ color: #569cd6; }}
        .log-tid {{ color: #4ec9b0; }}
        .log-level {{ font-weight: bold; padding: 0 3px; border-radius: 2px; }}
        .log-tag {{ color: #dcdcaa; font-weight: bold; }}
        .log-message {{ margin-left: 10px; }}
        .stats {{ background-color: #2d2d2d; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .filter-info {{ background-color: #3d3d3d; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Android Log Export</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total entries: {len(entries)}</p>
    </div>
"""

            if include_filters and filter_description:
                html_content += f"""
    <div class="filter-info">
        <h3>Applied Filters</h3>
        <p>{filter_description}</p>
    </div>
"""

            if analyzer:
                stats = analyzer.get_summary_stats()
                html_content += f"""
    <div class="stats">
        <h3>Session Statistics</h3>
        <p>Total Logs: {stats['total_logs']}</p>
        <p>Session Duration: {stats['session_duration_seconds']:.1f} seconds</p>
        <p>Error Rate: {stats['error_percentage']:.1f}%</p>
        <p>Unique Tags: {stats['unique_tags']}</p>
    </div>
"""

            html_content += """
    <div class="logs">
"""

            for entry in entries:
                level_color = color_map.get(entry.level.value.lower(), '#FFFFFF')
                timestamp_str = entry.timestamp.strftime('%m-%d %H:%M:%S.%f')[:-3]

                html_content += f"""
        <div class="log-entry" style="background-color: rgba(255,255,255,0.02);">
            <span class="log-timestamp">{timestamp_str}</span>
            <span class="log-pid">{entry.process_id:5d}</span>
            <span class="log-tid">{entry.thread_id:5d}</span>
            <span class="log-level" style="background-color: {level_color};">{entry.level.value}</span>
            <span class="log-tag">{entry.tag}:</span>
            <span class="log-message">{entry.message}</span>
        </div>
"""

            html_content += """
    </div>
</body>
</html>
"""

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return True
        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            return False

    def generate_report(self, entries: List[LogEntry], analyzer: LogAnalyzer,
                       filepath: str, filter_description: str = "") -> bool:
        """Generate comprehensive analysis report"""
        try:
            stats = analyzer.get_summary_stats()
            anomalies = analyzer.detect_anomalies(entries)
            tag_categories = analyzer.get_tag_categories()

            report_content = f"""Android Device Log Analysis Report
{'='*50}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Session Duration: {stats['session_duration_seconds']:.1f} seconds

SUMMARY STATISTICS
{'-'*20}
Total Logs Processed: {stats['total_logs']:,}
Current Log Rate: {stats['logs_per_second_current']:.1f} logs/sec
Peak Log Rate: {stats['logs_per_second_peak']:.1f} logs/sec
Error Rate: {stats['error_percentage']:.2f}%

LOG LEVEL BREAKDOWN
{'-'*20}
"""

            for level, count in stats['level_breakdown'].items():
                percentage = (count / max(stats['total_logs'], 1)) * 100
                report_content += f"{level}: {count:,} ({percentage:.1f}%)\n"

            report_content += f"""

TOP TAGS
{'-'*10}
"""
            for tag, count in list(stats['top_tags'].items())[:10]:
                report_content += f"{tag}: {count}\n"

            report_content += f"""

TOP PROCESSES
{'-'*15}
"""
            for pid, count in list(stats['top_processes'].items())[:5]:
                report_content += f"PID {pid}: {count} logs\n"

            if stats['top_errors']:
                report_content += f"""

TOP ERROR MESSAGES
{'-'*20}
"""
                for error, count in list(stats['top_errors'].items())[:5]:
                    report_content += f"({count}x) {error[:80]}{'...' if len(error) > 80 else ''}\n"

            if anomalies:
                report_content += f"""

DETECTED ANOMALIES
{'-'*20}
"""
                for anomaly in anomalies:
                    report_content += f"[{anomaly['severity'].upper()}] {anomaly['description']}\n"

            report_content += f"""

TAG CATEGORIES
{'-'*15}
System Tags ({len(tag_categories['system'])}): {', '.join(tag_categories['system'][:10])}
Framework Tags ({len(tag_categories['framework'])}): {', '.join(tag_categories['framework'][:10])}
Application Tags ({len(tag_categories['application'])}): {', '.join(tag_categories['application'][:10])}
Custom Tags ({len(tag_categories['custom'])}): {', '.join(tag_categories['custom'][:10])}

FILTERS APPLIED
{'-'*15}
{filter_description if filter_description else 'No filters applied'}
"""

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)

            return True
        except Exception as e:
            print(f"Error generating report: {e}")
            return False
