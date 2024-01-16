import datetime
import json
import sys
import time
from pathlib import Path

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


def download_pdf(url, pdf_file):
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


def download_pdfs(merged_json_file, pdfs_dir):
    merged_infos = json.loads(merged_json_file.read_text())

    pdf_infos_file = pdfs_dir / "pdfs.json"
    if pdf_infos_file.exists():
        pdf_infos = json.loads((pdf_infos_file).read_text())
    else:
        pdf_infos = []

    pdf_codes = set(p["Unique Code"] for p in pdf_infos)
    new_infos = [i for i in merged_infos if i["Unique Code"] not in pdf_codes]

    if new_infos:
        doc_dir = Path("import/documents")
        for dept_dir in DeptDirs:
            (doc_dir / dept_dir).mkdir(exist_ok=True)

    for info in new_infos:
        code, url = info["Unique Code"], info["Download"]
        assert code in url
        dept_dir_name = info["Department Name"].replace(" ", "_").replace("&", "and")
        pdf_dept_dir = pdfs_dir / dept_dir_name
        pdf_file = pdf_dept_dir / f"{code}.pdf"

        pdf_info = {
            "Unique Code": info["Unique Code"],
            "url": url,
            "status": "",
        }

        if not pdf_dept_dir.exists():
            print(f"{pdf_dept_dir} not found")
            pdf_info["download_success"] = False
            pdf_info["status"] = "dept_dir_missing"
        elif pdf_file.exists():
            pdf_info["download_dir"] = pdf_dept_dir.name

            m_time = pdf_file.stat().st_mtime
            m_time_utc = datetime.datetime.fromtimestamp(m_time, tz=datetime.timezone.utc)

            pdf_info["download_time_utc"] = m_time_utc.strftime("%Y-%m-%d %H:%M:%S %Z%z")
            pdf_info["download_success"] = True
            pdf_info["status"] = "downloaded_prior"
        else:
            d_success, d_utc_str = download_pdf(url, pdf_file)
            pdf_info["download_dir"] = pdf_dept_dir.name
            if d_success:
                pdf_info["download_time_utc"] = d_utc_str
                pdf_info["download_success"] = True
                pdf_info["status"] = "downloaded"
            else:
                pdf_info["download_success"] = False
                pdf_info["status"] = f"download_failed_{d_utc_str}"
        pdf_infos.append(pdf_info)
        pdf_infos_file.write_text(json.dumps(pdf_infos))
    # end for


if len(sys.argv) < 3:
    print("Usage: {sys.argv[0]} <merged_json_file> <pdfs_dir>")
    sys.exit(1)


merged_json_file = Path(sys.argv[1])
pdfs_dir = Path(sys.argv[2])
download_pdfs(merged_json_file, pdfs_dir)
