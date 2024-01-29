import json  # noqa
import os.path
import shutil
import sys
from collections import Counter
from datetime import date, datetime, timezone
from itertools import groupby
from operator import itemgetter
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from more_itertools import first
from unidecode import unidecode

"""
- url: ../Site/Upload/Government%20Resolutions/English/201903082134187101.pdf
  dept: Agriculture, Dairy Development, Animal Husbandry and Fisheries Department
  text: Promotion of Supervisor (Group-C) to Agriculture Officer, Maharashtra Agriculture
    Services (Group- B) (Junior)
  code: '201903082134187101'
  date: 08-03-2019
  size_kb: '3429'


- code: '202312291257005601'
  crawl_dir: 30-Dec-2023
  date: 29-12-2023
  dept: Agriculture, Dairy Development, Animal Husbandry and Fisheries Department
  download_time: '2023-12-30T00:26:23.034850'
  file_path: ../www.maharashtra.gov.in/Agriculture/30-Dec-2023/202312291257005601.pdf
  size_kb: '150'
  text: Release of funds difference in amount between Government declare Minimum Support
    Prize (MSP) and Agriculture Produce Market Committee (APMC) based rate in prescribed
    period of Seed Producing Farmers
url: https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/English/202312291257005601.pdf


 {
    "SN": "274",
    "Department Name": "Women and Child Development Department",
    "Title": "Disbursement of Yojana (2235 B183) for the Current Financial Year 2023-24.",
    "Unique Code": "202401171806298830",
    "G.R. Date": "17-01-2024",
    "File Size (KB)": "144",
    "Download": "https://gr.maharashtra.gov.in/Site/Upload/Govent%20Resolutions/English/202401171806298830.pdf",
    "download_dir": "20-Jan-2024_v1",
    "html_file": "17-Jan-2024_20-Jan-2024-27.html",
    "download_time_utc": "2024-01-20 19:43:37 UTC+0000"
  }
"""

DeptNames = {
    "Agriculture": "Agriculture, Dairy Development, Animal Husbandry and Fisheries Department",
    "Cooperative": "Co-operation, Textiles and Marketing Department",
    "Environment": "Environment Department",
    "Finance": "Finance Department",
    "Food": "Food, Civil Supplies and Consumer Protection Department",
    "Admin": "General Administration Department",
    "TechEdu": "Higher and Technical Education Department",
    "Home": "Home Department",
    "Housing": "Housing Department",
    "Industries": "Industries, Energy and Labour Department",
    "IT": "Information Technology Department",
    "Law": "Law and Judiciary Department",
    "Marathi": "Marathi Language Department",
    "MedicalEdu": "Medical Education and Drugs Department",
    "Minorities": "Minorities Development Department",
    "Bahujan": "Other Backward Bahujan Welfare Department",
    "Parliamentary": "Parliamentary Affairs Department",
    "Disability": "Persons with Disabilities Welfare Department",
    "Planning": "Planning Department",
    "Health": "Public Health Department",
    "PWD": "Public Works Department",
    "Revenue": "Revenue and Forest Department",
    "Rural": "Rural Development Department",
    "Education": "School Education and Sports Department",
    "Skill": "Skill Development and Entrepreneurship Department",
    "SocialJustice": "Social Justice and Special Assistance Department",
    "Soil": "Soil and Water Conservation Department",
    "Tourism": "Tourism and Cultural Affairs Department",
    "Tribal": "Tribal Development Department",
    "Urban": "Urban Development Department",
    "WaterResources": "Water Resources Department",
    "WaterSanitation": "Water Supply and Sanitation Department",
    "Women": "Women and Child Development Department",
}


def get_date(dir_name):
    date_format = "%d-%b-%Y"
    return datetime.strptime(dir_name.name, date_format).date()


def get_date_file_exists(info):
    file_size = info["pdf_file"].stat().st_size if info["pdf_file"] else -1

    # Multiplying by -1 so that info that have valid file come first
    return (-1 * file_size, get_date(info["download_dir"]))


MissingPDFs, BadHtml = 0, 0
MissingPDFInfos = []


def handle_date_dir(pdf_dir, dept_dir):
    def update_info(info):
        global MissingPDFs, BadHtml
        info["code"] = info["code"].strip(". ")
        info["code"] = info["code"]

        # assert info["code"].isascii()

        info["download_dir"] = pdf_dir

        if info["code"] not in html_dict:
            BadHtml = +1
            return None

        info["SN"], info["html_file"] = html_dict[info["code"]]

        if info.get("file_path", None):
            info["pdf_file"] = pdf_dir / Path(info["file_path"]).name
            info["pdf_file"] = info["pdf_file"] if info["pdf_file"].exists() else None
        else:
            info["pdf_file"] = None

        if not info["pdf_file"]:
            info["pdf_file"] = pdf_dict.get(info["code"], None)

        if info["pdf_file"]:
            mtime = info["pdf_file"].stat().st_mtime
            info["download_time_utc"] = datetime.fromtimestamp(mtime, timezone.utc)
        else:
            MissingPDFInfos.append((info["code"], info["html_file"]))
            MissingPDFs += 1
            info["download_time_utc"] = None
        return info

    def get_sn_code(html_file):
        global BadHtml
        soup = BeautifulSoup(html_file.read_text(), "html.parser")
        tables = soup.findAll("table")
        if len(tables) < 2:
            BadHtml += 1
            return []

        assert len(tables) >= 2

        sn_codes = []
        for row_idx, row in enumerate(tables[1].find_all("tr")):
            if row_idx == 0:
                continue
            row_vals = [td.text.strip() for td in row.find_all("td")]
            sn_codes.append((row_vals[0], row_vals[3].strip(". ")))
        return sn_codes

    def map_info(info):
        new_info = {}
        fs = [
            ("SN", "SN"),
            ("Department Name", "dept"),
            ("Title", "text"),
            ("Unique Code", "code"),
            ("G.R. Date", "date"),
            ("File Size", "size_kb"),
            ("Download", "url"),
            ("download_dir", "download_dir"),
            ("html_file", "html_file"),
            ("download_time_utc", "download_time_utc"),
            ("pdf_file", "pdf_file"),
        ]

        for new, old in fs:
            new_info[new] = info[old]

        if new_info['Download'].startswith('../'):
            new_info['Download'] = f'https://gr.maharashtra.gov.in{new_info["Download"][2:]}'
        
        return new_info

    url_file = pdf_dir / "urls.yml"
    if not url_file.exists():
        return []

    url_infos = yaml.load(url_file.read_text(), Loader=yaml.FullLoader)
    url_infos = [i for i in url_infos if i['dept'] == DeptNames[dept_dir.name]]
    html_dict = {}
    for html_file in pdf_dir.glob("**/*.html"):
        sn_codes = get_sn_code(html_file)
        html_dict.update(dict((c, (sn, html_file)) for (sn, c) in sn_codes))

    pdf_dict = dict((p.stem.strip(". "), p) for p in pdf_dir.glob("**/*.pdf"))

    url_infos = [update_info(i) for i in url_infos]
    url_infos = [map_info(i) for i in url_infos if i is not None]
    return url_infos


def clean_code(code):
    return unidecode(code).strip(" .")


def copy_infos(dept_crawl_infos, output_crawl_dir, GR_dir):
    if not output_crawl_dir.exists():
        output_crawl_dir.mkdir(exist_ok=True)

    for info in dept_crawl_infos:
        shutil.copy2(info["html_file"], output_crawl_dir)

        code = clean_code(info["Unique Code"])
        info["Unique Code"] = code
        if info["pdf_file"] and info["pdf_file"].stat().st_size > 0:
            dept_dir_name = info["Department Name"].replace(" ", "_").replace("&", "and")
            dept_dir = GR_dir / dept_dir_name
            assert dept_dir.exists()

            pdf_link_path = dept_dir / Path(code[:4]) / f"{code}.pdf"
            pdf_link_path.parent.mkdir(exist_ok=True, parents=True)

            src_path = os.path.relpath(str(info["pdf_file"]), start=str(pdf_link_path.parent))
            #pdf_link_path.symlink_to(Path(src_path))
            info["pdf_file"] = f"{dept_dir_name}/{code[:4]}/{pdf_link_path.name}"
        else:
            info["pdf_file"] = None

        info["download_dir"] = str(output_crawl_dir)
        info["html_file"] = info["html_file"].name
        t_utc = info["download_time_utc"]
        info["download_time_utc"] = t_utc.strftime("%Y-%m-%d %H:%M:%S %Z%z") if t_utc else None


website_dir = Path(sys.argv[1])
dept_dirs = [d for d in website_dir.glob("*") if d.is_dir()]
output_dir = Path(sys.argv[2])
GR_dir = Path(sys.argv[3])


def main():
    for dept_dir in dept_dirs:
        print(f"processing {dept_dir.name}")
        crawl_dirs = [d for d in dept_dir.glob("*") if d.is_dir()]
        crawl_dirs = sorted(crawl_dirs, key=get_date)

        dept_infos = set()
        for crawl_dir in crawl_dirs:
            infos = handle_date_dir(crawl_dir)

            # remove duplicates in the same file, shouldn't be
            dept_crawl_infos = {i["Unique Code"]: i for i in infos}.values()

            dept_crawl_infos = [i for i in dept_crawl_infos if i["Unique Code"] not in dept_infos]

            if dept_crawl_infos:
                output_crawl_dir = output_dir / crawl_dir.name
                copy_infos(dept_crawl_infos, (output_crawl_dir), GR_dir)
                dept_infos.update([i["Unique Code"] for i in dept_crawl_infos])

                json_path = output_crawl_dir / "GRs_old_log.json"
                log_infos = json.loads(json_path.read_text()) if json_path.exists() else []
                log_codes = set(i["Unique Code"] for i in log_infos)
                for info in dept_crawl_infos:
                    if info["Unique Code"] not in log_codes:
                        log_infos.append(info)

                json_path.write_text(json.dumps(log_infos))

        print(f"\tMissingPDFs={MissingPDFs}, BadHtml={BadHtml}")

    for code, html_file in MissingPDFInfos:
        print(f"{code}|{html_file}")


def main2():
    for dept_dir in dept_dirs:
        print(f"processing {dept_dir.name}")
        crawl_dirs = [d for d in dept_dir.glob("*") if d.is_dir()]
        crawl_dirs = sorted(crawl_dirs, key=get_date)

        dept_infos = {}
        for crawl_dir in crawl_dirs:
            infos = handle_date_dir(crawl_dir, dept_dir)
            for info in infos:
                info["Unique Code"] = clean_code(info["Unique Code"])
                dept_infos.setdefault(info["Unique Code"], []).append(info)

        dept_uniq_infos = []
        for code, code_infos in dept_infos.items():
            code_infos.sort(key=get_date_file_exists)
            dept_uniq_infos.append(first(code_infos))

        dept_uniq_infos.sort(key=itemgetter("download_dir"))
        for crawl_dir, dept_crawl_infos in groupby(dept_uniq_infos, itemgetter("download_dir")):
            output_crawl_dir = output_dir / crawl_dir.name

            dept_crawl_infos = list(dept_crawl_infos)
            copy_infos(dept_crawl_infos, output_crawl_dir, GR_dir)

            json_path = output_crawl_dir / "GRs_old_log.json"
            log_infos = json.loads(json_path.read_text()) if json_path.exists() else []
            log_codes = set(i["Unique Code"] for i in log_infos)
            for info in dept_crawl_infos:
                if info["Unique Code"] not in log_codes:
                    log_infos.append(info)
                else:
                    print(f'Duplicate Found {info["Unique Code"]}')

            json_path.write_text(json.dumps(log_infos))
        print(f"\tMissingPDFs={MissingPDFs}, BadHtml={BadHtml}")
    for code, html_file in MissingPDFInfos:
        print(f"{code}|{html_file}")


if __name__ == "__main__":
    main2()
