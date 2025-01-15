import datetime
import json
import os
import sys
import time
from pathlib import Path

import internetarchive as ia
import requests

DeptDirs = [
    "Agriculture,_Dairy_Development,_Animal_Husbandry_and_Fisheries_Department/",
    "Co-operation,_Textiles_and_Marketing_Department/",
    "Environment_Department/",
    "Finance_Department/",
    "Food,_Civil_Supplies_and_Consumer_Protection_Department/",
    "General_Administration_Department/",
    "Higher_and_Technical_Education_Department/",
    "Home_Department/",
    "Housing_Department/",
    "Industries,_Energy_and_Labour_Department/",
    "Information_Technology_Department/",
    "Law_and_Judiciary_Department/",
    "Marathi_Language_Department/",
    "Medical_Education_and_Drugs_Department/",
    "Minorities_Development_Department/",
    "Other_Backward_Bahujan_Welfare_Department/",
    "Parliamentary_Affairs_Department/",
    "Persons_with_Disabilities_Welfare_Department/",
    "Planning_Department/",
    "Public_Health_Department/",
    "Public_Works_Department/",
    "Revenue_and_Forest_Department/",
    "Rural_Development_Department/",
    "School_Education_and_Sports_Department/",
    "Skill_Development_and_Entrepreneurship_Department/",
    "Social_Justice_and_Special_Assistance_Department/",
    "Soil_and_Water_Conservation_Department/",
    "Tourism_and_Cultural_Affairs_Department/",
    "Tribal_Development_Department/",
    "Urban_Development_Department/",
    "Water_Resources_Department/",
    "Water_Supply_and_Sanitation_Department/",
    "Women_and_Child_Development_Department/",
]


def request_pdf(url, pdf_file):
    downloaded, dt_str = False, None
    try:
        print(f"Downloading {url}")
        r = requests.get(url)
        if r.status_code == 200:
            with pdf_file.open("wb") as f:
                f.write(r.content)
            downloaded = True
            dt_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z%z")
        else:
            print(f"An error occurred while downloading {url} Status: {r.status_code}")
    except Exception as e:
        print(f"An exception occurred while downloading {url}: {e}")

    time.sleep(2)
    return downloaded, dt_str


def get_pdf_path(merged_info, pdfs_dir):
    code, dept = merged_info["Unique Code"], merged_info["Department Name"]
    dept_dir_name = dept.replace(" ", "_").replace("&", "and")
    pdf_dept_dir = pdfs_dir / dept_dir_name / Path(code[:4])
    pdf_dept_dir.mkdir(parents=True, exist_ok=True)    
    pdf_file = pdf_dept_dir / f"{code}.pdf"
    return pdf_file


def download_pdf(pdfs_dir, merged_info):
    url = merged_info["Download"]
    # assert code in url
    pdf_file = get_pdf_path(merged_info, pdfs_dir)

    assert not pdf_file.exists()

    if not pdf_file.parent.exists():
        print(f"{pdf_file.parent} not found")
        return None, None
    else:
        d_success, d_utc_str = request_pdf(url, pdf_file)
        return (pdf_file, d_utc_str) if d_success else (None, d_utc_str)


def upload_internet_archive(info, pdf_path):
    md = info
    code = info["Unique Code"]

    # fmt: off
    descriptions = []
    descriptions += [ f'<td style="vertical-align: top"><b>Title</b>:</td> <td style="vertical-align: top">{md["Title"]}</td>' ]  # noqa
    descriptions += [ f'<td style="vertical-align: top"><b>Department</b>:</td> <td style="vertical-align: top">{md["Department Name"]}</td>' ] # noqa
    descriptions += [ f'<td style="vertical-align: top"><b>Code</b>:</td> <td style="vertical-align: top">{code}</td>' ] # noqa
    descriptions += [ f'<td style="vertical-align: top"><b>URL</b>:</td> <td style="vertical-align: top"> <a href="{md["url"]}">gr.maharashtra.gov.in</a></td>' ] # noqa
    if md["wayback_url"]:
        descriptions += [ f'<td style="vertical-align: top"><b>WaybackURL</b>:&nbsp;</td> <td style="vertical-align: top"> <a href="{md["wayback_url"]}">web.archive.org</a></td>' ] # noqa

    # fmt: on
    description = "<b>Maharashtra Government Resolution<b>:<p>"
    description += "<table>\n<tr>" + "</tr>\n<tr>".join(descriptions) + "</tr>\n</table>\n"
    metadata = {
        "collection": "maharashtragr",
        "mediatype": "texts",
        "title": f"Maharashtra GR: #{code}",
        "topics": "Maharashtra Government Resolutions",
        "date": md["G.R. Date"],
        "creator": "Government of Maharashtra",
        "description": description,
        "subject": ["Maharasthra Government Resolutions", md["Department Name"]],
        "language": ["Marathi", "English"],
        "department": md["Department Name"],
        "url": md["url"],
        "wayback_url": md["wayback_url"],
        "unique_code": code,
    }
    identifier = f"in.gov.maharashtra.gr.{code}"
    print("\tSaving on archive")

    access_key = os.environ.get("IA_ACCESS_KEY", "")
    secret_key = os.environ.get("IA_SECRET_KEY", "")

    pdf_path = str(pdf_path)
    try:
        if access_key and secret_key:
            config = {"s3": {"access": access_key, "secret": secret_key}}
            item = ia.get_item(identifier, config)
            responses = item.upload(
                pdf_path,
                metadata=metadata,
                access_key=access_key,
                secret_key=secret_key,
                validate_identifier=True,
            )
        else:
            item = ia.get_item(identifier)
            responses = item.upload(pdf_path, metadata=metadata, validate_identifier=True)

    except Exception as e:
        print(f"Exeption as {e}")
        return None, None

    archive_url = responses[0].url
    print(f"**Uploaded: {identifier} {archive_url}\n")
    return archive_url, identifier


def get_file_path(gr_info):
    name = gr_info["name"]
    repo, _ = name.split("-")
    file_path = Path(f"../{repo}/import/documents/{name}")
    file_path = file_path.resolve()
    return file_path


def upload_all_internet_archive(merged_json_file, wayback_json_file, archive_json_file, pdfs_dir):
    merged_infos = json.loads(merged_json_file.read_text())
    wayback_infos = json.loads(wayback_json_file.read_text())
    archive_infos = json.loads(archive_json_file.read_text()) if archive_json_file.exists() else []

    wayback_info_dict = dict((w["Unique Code"], w) for w in wayback_infos)
    archive_codes = set(a["Unique Code"] for a in archive_infos)

    new_infos = [i for i in merged_infos if i["Unique Code"] not in archive_codes]
    # new_infos = [i for i in merged_infos if i["Unique Code"] not in archive_codes]

    if new_infos:
        for dept_dir in DeptDirs:
            (pdfs_dir / dept_dir).mkdir(exist_ok=True)
            (pdfs_dir / dept_dir / Path("2024")).mkdir(exist_ok=True)

    print(f"*** New infos: {len(new_infos)}")
    for idx, info in enumerate(new_infos):
        code = info["Unique Code"]
        print(f"*** Uploading {code} [{idx}/{len(new_infos)}]")

        wayback_info = wayback_info_dict.get(code, None)

        info["url"] = info["Download"]
        info["wayback_url"] = wayback_info.get("archive_url", "") if wayback_info else ""

        pdf_file = get_pdf_path(info, pdfs_dir)

        if not pdf_file.exists():
            (pdf_file, download_date_utc) = download_pdf(pdfs_dir, info)

        if not pdf_file:
            info["upload_success"] = False
            print("Failed")
        else:
            archive_url, identifier = upload_internet_archive(info, pdf_file)
            if archive_url:
                info["archive_url"] = archive_url
                info["identifier"] = identifier
                info["upload_success"] = True
                print(f"Success: {archive_url}")
            else:
                info["upload_success"] = False
                print("Failed")

        archive_infos.append(info)
        archive_json_file.write_text(json.dumps(archive_infos))


def update_all_internet_archive(merged_json_file, wayback_json_file, archive_json_file, pdfs_dir):
    wayback_infos = json.loads(wayback_json_file.read_text())
    wayback_info_dict = dict((w["Unique Code"], w) for w in wayback_infos)
    archive_infos = json.loads(archive_json_file.read_text())

    for info in archive_infos:
        if info.get("upload_success", False):
            continue

        if "identifier" in info:
            info["upload_success"] = True
            continue

        code = info["Unique Code"]
        wayback_info = wayback_info_dict.get(code, None)
        info["wayback_url"] = wayback_info.get("archive_url", "") if wayback_info else ""

        pdf_file = get_pdf_path(info, pdfs_dir)
        if not pdf_file.exists():
            (pdf_file, download_date_utc) = download_pdf(pdfs_dir, info)

        if not pdf_file:
            continue
        else:
            archive_url, identifier = upload_internet_archive(info, pdf_file)
            if archive_url:
                info["archive_url"] = archive_url
                info["identifier"] = identifier
                info["upload_success"] = True
            else:
                continue
        archive_json_file.write_text(json.dumps(archive_infos))


def main():
    merged_json_file = Path(sys.argv[1])
    wayback_json_file = Path(sys.argv[2])
    archive_json_file = Path(sys.argv[3])
    pdf_dir = Path(sys.argv[4])

    upload_all_internet_archive(merged_json_file, wayback_json_file, archive_json_file, pdf_dir)


main()
