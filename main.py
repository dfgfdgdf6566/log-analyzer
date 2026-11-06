import argparse
import json
import csv
import sys
from datetime import datetime

def parse_line(line, line_num):
    parts = [p.strip() for p in line.split('|')]
    if len(parts) != 5:
        return None, f"Line {line_num}: invalid format (expected 5 fields)"
    
    ts_str, level, source, code, msg = parts
    if not ts_str or not level or not source or not code or not msg:
        return None, f"Line {line_num}: empty fields"
    
    try:
        ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None, f"Line {line_num}: invalid timestamp"
    
    if level not in ["TRACE", "DEBUG", "INFO", "WARN", "ERROR"]:
        return None, f"Line {line_num}: invalid level"
    
    return {
        "timestamp": ts,
        "level": level,
        "source": source,
        "code": code,
        "message": msg
    }, None

def main():
    parser = argparse.ArgumentParser(description="Log Analyzer")
    parser.add_argument("--input", required=True, help="Path to log file")
    parser.add_argument("--from", dest="from_ts", help="Start time (ISO 8601)")
    parser.add_argument("--to", dest="to_ts", help="End time (ISO 8601)")
    parser.add_argument("--level", help="Filter by level")
    parser.add_argument("--source", help="Filter by source")
    parser.add_argument("--top", type=int, default=10, help="Top N error codes")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()

    from_dt = datetime.strptime(args.from_ts, "%Y-%m-%dT%H:%M:%SZ") if args.from_ts else None
    to_dt = datetime.strptime(args.to_ts, "%Y-%m-%dT%H:%M:%SZ") if args.to_ts else None

    total_lines = 0
    valid_lines = 0
    invalid_lines = 0
    errors = []
    filtered_events = 0
    by_level = {}
    by_source = {}
    error_codes = {}

    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                total_lines += 1
                event, err = parse_line(line, line_num)
                if err:
                    invalid_lines += 1
                    errors.append(err)
                    continue
                valid_lines += 1

                # Apply filters
                if from_dt and event["timestamp"] < from_dt: continue
                if to_dt and event["timestamp"] >= to_dt: continue
                if args.level and event["level"] != args.level: continue
                if args.source and event["source"] != args.source: continue

                filtered_events += 1
                by_level[event["level"]] = by_level.get(event["level"], 0) + 1
                by_source[event["source"]] = by_source.get(event["source"], 0) + 1
                if event["level"] == "ERROR":
                    error_codes[event["code"]] = error_codes.get(event["code"], 0) + 1

    except FileNotFoundError:
        print(f"Error: File '{args.input}' not found.")
        sys.exit(1)

    top_errors = sorted(error_codes.items(), key=lambda x: (-x[1], x[0]))[:args.top]

    result = {
        "total_lines": total_lines,
        "valid_lines": valid_lines,
        "invalid_lines": invalid_lines,
        "errors": errors,
        "filtered_events": filtered_events,
        "by_level": by_level,
        "by_source": by_source,
        "top_error_codes": top_errors
    }

    # Print to terminal
    print(f"Total lines: {total_lines}")
    print(f"Valid: {valid_lines}, Invalid: {invalid_lines}")
    print(f"Filtered events: {filtered_events}")
    print("By level:", by_level)
    print("By source:", by_source)
    print("Top errors:", top_errors)

    if args.output:
        if args.format == "json":
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        elif args.format == "csv":
            with open(args.output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Total lines", total_lines])
                writer.writerow(["Valid lines", valid_lines])
                writer.writerow(["Invalid lines", invalid_lines])
                writer.writerow(["Filtered events", filtered_events])

if __name__ == "__main__":
    main()
