import json
import sys
from pathlib import Path


def main():
    merged_json_file = Path(sys.argv[1])
    wayback_json_file = Path(sys.argv[2])
    archive_json_file = Path(sys.argv[3])

    export_json_file = Path(sys.argv[4])

    export_infos = json.loads(export_json_file.read_text()) if export_json_file.exists() else []
    export_ids = set(i["Unique Code"] for i in export_infos)

    merged_infos = json.loads(merged_json_file.read_text())
    new_infos = [i for i in merged_infos if i["Unique Code"] not in export_ids]

    print(f"New Infos: {len(new_infos)}")

    if new_infos:
        wayback_dict = {i["Unique Code"]: i for i in json.loads(wayback_json_file.read_text())}
        archive_dict = {i["Unique Code"]: i for i in json.loads(archive_json_file.read_text())}

        for info in new_infos:
            code = info["Unique Code"]
            wayback_info, archive_info = wayback_dict.get(code, None), archive_dict.get(code, None)

            if wayback_info and wayback_info.get("link_success"):
                info["wayback"] = {
                    "url": wayback_info["archive_url"],
                    "sha1": wayback_info["archive_sha1"],
                    "length": wayback_info["archive_length"],
                    "status": True,
                }
            else:
                info["wayback_info"] = {"status": False}

            if archive_info and archive_info["upload_success"]:
                info["archive"] = {
                    "url": archive_info["archive_url"],
                    "identifier": archive_info["identifier"],
                    "status": True,
                }
            else:
                info["archive_info"] = {"status": False}
            export_infos.append(info)
        export_json_file.write_text(json.dumps(export_infos))


main()
