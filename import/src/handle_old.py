from pathlib import Path
import os

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
    "Title": "Disbursement of Rs.10.00 Crore for the Revised Manodhairya Yojana (2235 B183) for the Current Financial Year 2023-24.",
    "Unique Code": "202401171806298830",
    "G.R. Date": "17-01-2024",
    "File Size (KB)": "144",
    "Download": "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/English/202401171806298830.pdf",
    "download_dir": "20-Jan-2024_v1",
    "html_file": "17-Jan-2024_20-Jan-2024-27.html",
    "download_time_utc": "2024-01-20 19:43:37 UTC+0000"
  }
"""

def handle_date_dir(pdf_dir):
    url_infos = yaml.load(pdf_dir / 'urls.yml', Loader=yaml.FullLoader)
    
    
