import datetime
import json
import sys
from pathlib import Path

import traverser as trav


def get_date_str(date_obj):
    return date_obj.strftime("%d-%b-%Y")


def parse_date(date_str):
    # months = 'jan-feb-mar-apr-may-jun-jul-aug-sep-oct-nov-dec'.split('-')
    d, m, y = date_str.split("-")
    return datetime.date(year=int(y), month=int(m), day=int(d))


def save_doc_infos(doc_infos, output_dir):
    (output_dir / "GRs_log.json").write_text(json.dumps(doc_infos))


MaxPages = 1000
BaseURL = "https://gr.maharashtra.gov.in"


def get_additional_cols(crawler, table_id):
    def get_cell(row_idx, col_idx):
        r, c = row_idx, col_idx
        # increase row count by 2 (idx==0, and idx==1 is header)
        cells = table.query_selector_all(f"tr:nth-child({r + 2}) td:nth-child({c + 1})")
        assert len(cells) == 1
        return cells[0].inner_text().strip()

    tables = crawler.get_tables(id_regex=table_id)
    assert len(tables) == 1
    table = tables[0]

    row_count, col_vals = len(table.query_selector_all("tr")), {}
    row_count -= 1  # remove the header

    for idx, field in enumerate(["dept", "text", "code", "date", "size_kb"]):
        col_idx = idx + 1
        cells = [get_cell(row_idx, col_idx) for row_idx in range(row_count)]
        col_vals[field] = cells

    return col_vals


def fetch_site(crawler, start_date, end_date, output_dir):
    def strip_row(row):
        row = [c.strip() if c else c for c in row]
        row[3] = row[3].strip(".")
        return row

    print(f"Output_dir: {output_dir}")

    crawler.click(text="English", ignore_error=True)
    crawler.wait(2)

    crawler.set_form_element("SitePH_txtFromDate", start_date.strftime("%d %b, %Y"))
    crawler.set_form_element("SitePH_txtToDate", end_date.strftime("%d %b, %Y"))
    crawler.wait(3)

    has_next = crawler.click(text="Next >")
    crawler.wait(5)
    crawler.click(text="< Previous")
    crawler.wait(3)

    abbr = f'{start_date.strftime("%d-%b-%Y")}_{end_date.strftime("%d-%b-%Y")}'

    doc_infos = []
    for start_idx in range(MaxPages):
        # crawler.save_screenshot(output_dir / f"{abbr}-{start_idx}.png")
        crawler.save_html(output_dir / f"{abbr}-{start_idx}.html")

        tables = crawler.get_tables(id_regex="SitePH_dgvDocuments")
        assert len(tables) == 1
        table = tables[0]

        dt = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z%z")
        for row_texts, row_links in zip(table.rows_texts, table.rows_links):
            row_texts = strip_row(row_texts)
            row_texts[-1] = row_links[-1][0].url
            doc_info = dict(zip(table.header, row_texts))
            doc_info["download_dir"] = output_dir.name
            doc_info["html_file"] = f"{abbr}-{start_idx}.html"
            doc_info["download_time_utc"] = dt
            doc_infos.append(doc_info)

        save_doc_infos(doc_infos, output_dir)

        has_next = crawler.click(text="Next >", ignore_error=True)
        if not has_next:
            print(f"Next page not found on Page Number: {start_idx}+")
            break
        crawler.wait(4)
    print(f"Done crawling: {abbr}")

MarathiEnglishDepartments = {
    "कृषी, पशुसंवर्धन, दुग्‍धव्‍यवसाय विकास व मत्‍स्‍यव्‍यवसाय विभाग": "Agriculture, Animal Husbandry, Dairy Development & Fisheries Department",
    "सहकार, पणन व वस्‍त्रोद्योग विभाग": "Co-operation, Marketing and Textiles Department",
    "कौशल्य विकास व उदयोजकता विभाग": "Skill Development and Entrepreneurship Department",
    "पर्यावरण विभाग": "Environment Department",
    "वित्त विभाग": "Finance Department",
    "अन्‍न, नागरी पुरवठा व ग्राहक संरक्षण विभाग": "Food, Civil Supplies and Consumer Protection Department",
    "सामान्य प्रशासन विभाग": "General Administration Department",
    "उच्च व तंत्र शिक्षण विभाग": "Higher and Technical Education Department",
    "गृहनिर्माण विभाग": "Housing Department",
    "उद्योग, उर्जा व कामगार विभाग": "Industries, Energy and Labour Department",
    "माहिती तंत्रज्ञान (सा.प्र.वि.) विभाग": "Information Technology (GAD) Department",
    "विधी व न्याय विभाग": "Law and Judiciary Department",
    "वैद्यकीय शिक्षण व औषधी द्रव्‍ये विभाग": "Medical Education and Drugs Department",
    "अल्पसंख्याक विकास विभाग": "Minority Development Department",
    "संसदीय कार्य विभाग": "Parliamentary Affairs Department",
    "नियोजन विभाग": "Planning Department",
    "सार्वजनिक आरोग्य विभाग": "Public Health Department",
    "सार्वजनिक बांधकाम विभाग": "Public Works Department",
    "महसूल व वन विभाग": "Revenue and Forest Department",
    "ग्राम विकास विभाग": "Rural Development Department",
    "शालेय शिक्षण व क्रीडा विभाग": "School Education and Sports Department",
    "सामाजिक न्‍याय व विशेष सहाय्य विभाग": "Social Justice and Special Assistance Department",
    "पर्यटन व सांस्कृतिक कार्य विभाग": "Tourism and Cultural Affairs Department",
    "आदिवासी विकास विभाग": "Tribal Development Department",
    "नगर विकास विभाग": "Urban Development Department",
    "मृद व जलसंधारण विभाग": "Soil and Water Conservation Department"
}

def get_dept(dept_name):
    if not dept_name.isascii() and dept_name in MarathiEnglishDepartments:
        MarathiEnglishDepartments[dept_name]
    return dept_name

def parse_date_hyphen(date_str):
    d, m, y = date_str.split('-')
    d, m, y = int(d), int(m), int(y)
    return datetime.date(year=y, month=m, day=d)

def fetch_site2(crawler, start_date, end_date, output_dir):
    def strip_row(row):
        row = [c.strip() if c else c for c in row]
        row[3] = row[3].strip(".")
        return row

    print(f"Output_dir: {output_dir}")

    crawler.click(text="English", ignore_error=True)
    crawler.wait(2)

    abbr = f'{start_date.strftime("%d-%b-%Y")}_{end_date.strftime("%d-%b-%Y")}'
    table_classes = "table table-striped table-bordered table-hover".split(' ')

    doc_infos = []
    for start_idx in range(MaxPages):
        # crawler.save_screenshot(output_dir / f"{abbr}-{start_idx}.png")
        crawler.save_html(output_dir / f"{abbr}-{start_idx}.html")

        tables = crawler.get_tables(class_regex=table_classes)
        assert len(tables) == 1
        table = tables[0]

        dt = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z%z")
        for row_texts, row_links in zip(table.rows_texts, table.rows_links):
            row_texts = strip_row(row_texts)
            doc_info = {}

            doc_info['SN'] = row_texts[0]
            doc_info['Department Name'] = get_dept(row_texts[1])
            doc_info['Title'] = row_texts[2]
            doc_info['Unique Code'] = row_texts[3]
            doc_info['G.R. Date'] = row_texts[4].replace('/', '-')
            doc_info['File Size (KB)'] =  None
            doc_info['Download'] = f'https://gr.maharashtra.gov.in/assets/public/{row_texts[3]}.pdf'
            doc_info["download_dir"] = output_dir.name
            doc_info["html_file"] = f"{abbr}-{start_idx}.html"
            doc_info["download_time_utc"] = dt
            doc_infos.append(doc_info)

        save_doc_infos(doc_infos, output_dir)
        last_row_date = parse_date_hyphen(doc_infos[-1]['G.R. Date'])

        if last_row_date < start_date:
            print(f'last_row_date: {last_row_date} end_date: {end_date}')
            break

        has_next = crawler.click_element(role=('button', 'Next page'))
        if not has_next:
            print(f"Next page not found on Page Number: {start_idx}+")
            break
        
        print('Waiting for page to load')
        crawler.wait(10)
    print(f"Done crawling: {abbr}")



#GovResolutionsURL = "https://gr.maharashtra.gov.in/1145/Government-Resolutions"
GovResolutionsURL = "https://gr.maharashtra.gov.in/#/Government-resolution"

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {sys.argv[0]} <website_dir> [<start_date> <end_date>]")
        sys.exit(1)

    today = datetime.date.today()
    months = "-jan-feb-mar-apr-may-jun-jul-aug-sep-oct-nov-dec".split("-")
    month_dir = months[today.month].capitalize()

    website_dir = Path(sys.argv[1]) / f"{month_dir}-{today.year}"
    website_dir.mkdir(exist_ok=True)

    if len(sys.argv) > 2:
        start_date = parse_date(sys.argv[2])
        to_date = parse_date(sys.argv[3])
    else:
        to_date = today
        start_date = to_date - datetime.timedelta(days=10)

    date_str = get_date_str(today)

    existing_dirs = list(website_dir.glob(f"{date_str}*"))
    output_dir = website_dir / f"{date_str}_v{len(existing_dirs)+1}"
    output_dir.mkdir(exist_ok=False)

    crawler = trav.start(GovResolutionsURL, output_dir / "logs.txt", headless=True)
    crawler.wait(10)
    fetch_site2(crawler, start_date, to_date, output_dir)

"""
 {
    "SN": "1",
    "Department Name": "Agriculture, Dairy Development, Animal Husbandry and Fisheries Department",
    "Title": "Regarding approval of the Annual Action Plan worth Rs. 20414.58 lakhs under the Agricultural Mechanization Sub-Mission for the year 2025-26.",
    "Unique Code": "202505021244567301",
    "G.R. Date": "02-05-2025",
    "File Size (KB)": "470",
    "Download": "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/English/202505021244567301....pdf",
    "download_dir": "02-May-2025_v1",
    "html_file": "30-Apr-2025_02-May-2025-0.html",
    "download_time_utc": "2025-05-02 16:45:11 UTC+0000"
  },

"File Size"
"Download"

"SN-अ. क्र.|Department Name-विभागाचे नाव|Title-शीर्षक|Unique Code-संकेतांक|G.R. Date-शासन निर्णय दिनांक|



p table.header
['अ. क्र.', 'विभागाचे नाव', 'शीर्षक', 'संकेतांक', 'शासन निर्णय दिनांक', 'क्यूआर कोड', 'पाहा /डाउनलोड करा']
(Pdb) n

# parse date




"""
