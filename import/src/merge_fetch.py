import json
import sys
from pathlib import Path


def merge_fetch(json_log_dir, merged_json_file):
    def get_size(p):
        return p.stat().st_size

    if merged_json_file.exists():
        merged_infos = json.loads(merged_json_file.read_text())
    else:
        merged_infos = []
    merged_codes = set(m["Unique Code"] for m in merged_infos)
    num_orig_infos = len(merged_infos)

    # pick bigger files first
    json_log_files = sorted(json_log_dir.glob("**/GRs_old_log.json"), key=get_size, reverse=True)
    for json_log_file in json_log_files:
        new_infos = json.loads(json_log_file.read_text())
        new_infos = [i for i in new_infos if i["Unique Code"] not in merged_codes]

        merged_infos += new_infos
        merged_codes.update(i["Unique Code"] for i in new_infos)

    merged_json_file.write_text(json.dumps(merged_infos))
    print(f"Added new infos: {len(merged_infos) - num_orig_infos}")


if len(sys.argv) < 3:
    print("Usage: {sys.argv[0]} <json_log_dir> <output_json>")
    sys.exit(1)

json_log_dir = Path(sys.argv[1])
merged_json_file = Path(sys.argv[2])

merge_fetch(json_log_dir, merged_json_file)
