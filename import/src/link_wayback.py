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


def main(merged_json_file, wayback_json_file):
    wayback_infos = json.loads(wayback_json_file.read_text()) if wayback_json_file.exists() else []
    wayback_codes = [w["Unique Code"] for w in wayback_infos]

    pdf_infos = json.loads(merged_json_file.read_text())
    new_infos = [i for i in pdf_infos if i["Unique Code"] not in wayback_codes]

    print(f"*** New infos: {len(new_infos)}")

    wayback_archive = WaybackArchive()
    for idx, pdf_info in enumerate(new_infos):
        print(f"**** {pdf_info['Unique Code']} [{idx}/{len(new_infos)}]")
        try:
            url = pdf_info["Download"]
            wayback_info = wayback_archive.get_archive_info(url, "newest")
            if not wayback_info:
                wayback_archive.save_url(url)
                wayback_info = wayback_archive.get_archive_info(url, "newest")
            # endif
            pprint(wayback_info)
            wayback_info["url"] = url
            wayback_info["Unique Code"] = pdf_info["Unique Code"]
            wayback_info["archive_time"] = wayback_info["archive_time"].strftime(
                "%Y-%m-%d %H:%M:%S %Z%z"
            )
            wayback_info["link_success"] = True
        except Exception as e:
            print(f"Wayback machine failed for url: {url} -> {e}")
            wayback_info = {"url": url, "Unique Code": pdf_info["Unique Code"]}
            wayback_info["link_success"] = False

        print()

        wayback_infos.append(wayback_info)
        wayback_json_file.write_text(json.dumps(wayback_infos))
        time.sleep(4)


def retry(merged_json_file, wayback_json_file):
    wayback_infos = json.loads(wayback_json_file.read_text())

    wayback_archive = WaybackArchive()
    for info in wayback_infos:
        if info.get("link_success", False):
            continue

        if "archive_sha1" in info:
            info["link_success"] = True
            continue

        assert not info["link_success"]

        print(f"**** {info['Unique Code']}")
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

        wayback_json_file.write_text(json.dumps(wayback_infos))
    wayback_json_file.write_text(json.dumps(wayback_infos))


if __name__ == "__main__":
    merged_json_file = Path(sys.argv[1])
    wayback_json_file = Path(sys.argv[2])

    main(merged_json_file, wayback_json_file)
    # retry(merged_json_file, wayback_json_file)
