""""
 {
    "SN": "1",
    "Department Name": "Agriculture, Dairy Development, Animal Husbandry and Fisheries Department",
    "Title": "Regarding approving the implementation of District Agricultural Festival Scheme in the year 2023-24..",
    "Unique Code": "202401101217404701",
    "G.R. Date": "10-01-2024",
    "File Size (KB)": "150",
    "Download": "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/English/202401101217404701.pdf",
    "download_dir": "12-Jan-2024_v4",
    "download_time_utc": "2024-01-12 06:21:19 UTC+0000",
    "url": "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/English/202401101217404701.pdf",
    "wayback_url": "https://web.archive.org/web/20240112102613/https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/English/202401101217404701.pdf",
    "upload_success": true,
    "archive_url": "http://s3.us.archive.org/in.gov.maharashtra.gr.202401101217404701/202401101217404701.pdf",
    "identifier": "in.gov.maharashtra.gr.202401101217404701"
  },
"""
import sys
import json

from pathlib import Path

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


archive_json_path = Path(sys.argv[1])
GR_dir = Path(sys.argv[2])

infos = json.loads(archive_json_path.read_text())
for info in  infos:
    dept_dir_name = info["Department Name"].replace(" ", "_").replace("&", "and")
    dept_dir = GR_dir / dept_dir_name
    pdf_path = dept_dir / Path(code[:4]) / f'{info["Unique Code"].pdf}'
    if not pdf_path.exists():
        if info['upload_success']:
            downloaded, _ = request_pdf(info['archive_url'], pdf_path)
        else:
            downloaded, _ = request_pdf(info['Download'], pdf_path)

        if not downloaded:
            print(f'Download Failed {info["Unique Code"]}')
#end for
            
        

    



