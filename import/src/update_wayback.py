import json
import sys
import time
from pathlib import Path
from pprint import pprint

from waybackpy import WaybackMachineCDXServerAPI, WaybackMachineSaveAPI, exceptions

# TODO
# 1. Multiple modes of execution 1) Get archive URL 2) Compare SHA 3) Upload if not present
# 2. Add functionality for upload if not present ( need asynchronous way of doing this)
# 3. ALlow retries for downloading the document with proper timeout (requests library).


class WaybackArchive:
    UserAgent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0"  # noqa
    )

    def get_content_url(self, archive_url):
        url_pos = archive_url[6:].index("https:") + len("https:") - 1
        content_url = archive_url[:url_pos] + "id_" + archive_url[url_pos:]
        return content_url

    def get_archive_info(self, url: str, age: str):
        assert age in ("newest", "oldest")

        cdx_api = WaybackMachineCDXServerAPI(url, self.UserAgent)

        try:
            newest = cdx_api.newest() if age == "newest" else cdx_api.oldest()
        except (exceptions.NoCDXRecordFound, ConnectionResetError) as e:  # noqa
            print(f"Unable to find {url} in wayback")
            return None

        content_url = self.get_content_url(newest.archive_url)
        return {
            "url": url,
            "archive_url": newest.archive_url,
            "content_url": content_url,
            "archive_time": newest.datetime_timestamp,
            "archive_sha1": newest.digest,
            "archive_status_code": newest.statuscode,
            "archive_length": newest.length,
            "archive_mimetype": newest.mimetype,
        }

    def save_url(self, url: str):
        save_api = WaybackMachineSaveAPI(url, user_agent=self.UserAgent, max_tries=3)
        save_api.save()
        print(f"SAVED: {save_api.archive_url}")
        # do get_archive_info after saving, as save_api does not contain sha and other info

SkipCodes = ['202401021749155221', '202401011906494521']

def update(merged_json_file, wayback_json_file):
    wayback_infos = json.loads(wayback_json_file.read_text())

    wayback_archive = WaybackArchive()
    for info in wayback_infos:
        if info.get("link_success", False):
            continue

        if "archive_sha1" in info:
            info["link_success"] = True
            continue

        assert not info["link_success"]

        code = info["Unique Code"]
        info["Unique Code"] = code = code.replace('\u200d', '')

        if code in SkipCodes:
            print(f'\tSkipping {code}')
            continue

        print(f"Processing {info['Unique Code']}")
        try:
            url = info["url"]
            wayback_info = wayback_archive.get_archive_info(url, "newest")
            if not wayback_info:
                wayback_archive.save_url(url)
                wayback_info = wayback_archive.get_archive_info(url, "newest")
            # endif
            pprint(wayback_info)
            wayback_info["archive_time"] = wayback_info["archive_time"].strftime(
                "%Y-%m-%d %H:%M:%S %Z%z"
            )
            for k, v in wayback_info.items():
                info[k] = v

            info["link_success"] = True
        except Exception as e:
            print(f"Wayback machine failed for url: {url} -> {e}")

        print()        
        wayback_json_file.write_text(json.dumps(wayback_infos))
        time.sleep(4)        
    wayback_json_file.write_text(json.dumps(wayback_infos))


if __name__ == "__main__":
    merged_json_file = Path(sys.argv[1])
    wayback_json_file = Path(sys.argv[2])

    update(merged_json_file, wayback_json_file)
