import json
import sys
import os
from pathlib import Path
import time

import internetarchive as ia

def upload_internet_archive(info, pdf_path):
    md = info
    code = info['Unique Code']

    descriptions = []
    descriptions += [ f'<td style="vertical-align: top"><b>Title</b>:</td> <td style="vertical-align: top">{md["Title"]}</td>' ]
    descriptions += [ f'<td style="vertical-align: top"><b>Department</b>:</td> <td style="vertical-align: top">{md["Department Name"]}</td>' ]
    descriptions += [ f'<td style="vertical-align: top"><b>Code</b>:</td> <td style="vertical-align: top">{code}</td>' ]    
    descriptions += [ f'<td style="vertical-align: top"><b>URL</b>:</td> <td style="vertical-align: top"> <a href=\"{md["url"]}\">gr.maharashtra.gov.in</a></td>' ]
    descriptions += [ f'<td style="vertical-align: top"><b>WaybackURL</b>:&nbsp;</td> <td style="vertical-align: top"> <a href=\"{md["wayback_url"]}\">web.archive.org</a></td>' ]

    description = '<b>Maharashtra Government Resolution<b>:<p>'
    description += '<table>\n<tr>' + "</tr>\n<tr>".join(descriptions) + '</tr>\n</table>\n'
    metadata = {
        'collection': 'maharashtragr',
        'mediatype': 'texts',        
        'title': f'Maharashtra GR: #{code}',
        'topics': 'Maharashtra Government Resolutions',
        'date': md['G.R. Date'],
        'creator': 'Government of Maharashtra',
        'description': description,
        'subject': ['Maharasthra Government Resolutions', md["Department Name"]],
        'language': ['Marathi', 'English'],
        'department': md["Department Name"],
        'url': md['url'],
        'wayback_url': md['wayback_url'],
        'unique_code': code,
    }

    file_name = f'{code}.pdf'
    identifier = f'in.gov.maharashtra.gr.{code}'
    print('\tSaving on archive')

    #access_key=os.environ['IA_ACCESS_KEY']
    #secret_key=os.environ['IA_SECRET_KEY']

    pdf_path = str(pdf_path)
    try:
        item = ia.get_item(identifier)
        responses = item.upload(pdf_path, metadata=metadata, validate_identifier=True)
    except Exception as e:
        return None, None
    
    archive_url = responses[0].url
    print(f'**Uploaded: {identifier} {archive_url}\n')
    return archive_url, identifier

def get_file_path(gr_info):
    name = gr_info['name']
    repo,_ = name.split('-')
    file_path = Path(f'../{repo}/import/documents/{name}')
    file_path = file_path.resolve()
    return file_path

def upload_all_internet_archive(merged_json_file, pdfs_file, wayback_json_file, archive_json_file):
    merged_infos = json.loads(merged_json_file.read_text())
    pdf_infos = json.loads(pdfs_file.read_text())
    wayback_infos = json.loads(wayback_json_file.read_text())
    archive_infos = json.loads(archive_json_file.read_text()) if archive_json_file.exists() else []

    pdf_info_dict = dict((p['Unique Code'], p) for p in pdf_infos)
    wayback_info_dict = dict((w['Unique Code'], w) for w in wayback_infos)

    archive_codes = set(a['Unique Code'] for a in archive_infos)
    new_infos = [i for i in merged_infos if i['Unique Code'] not in archive_codes]

    print(f'New infos: {len(new_infos)}')    

    for info in new_infos:
        code = info['Unique Code']
        pdf_info, wayback_info = pdf_info_dict.get(code, None), wayback_info_dict.get(code, None)
        if pdf_info and pdf_info['download_success']:
            info['url'] = pdf_info['url']
            info['wayback_url'] = wayback_info.get('archive_url', '') if wayback_info else ''

            pdf_path = pdfs_file.parent / Path(pdf_info['download_dir']) / f'{code}.pdf'
            archive_url, identifier = upload_internet_archive(info, pdf_path)
            if archive_url:
                info['archive_url'] = archive_url
                info['identifier'] = identifier
                info['upload_success'] = True                
            else:
                info['upload_success'] = False
            
            archive_infos.append(info)
            archive_json_file.write_text(json.dumps(archive_infos))

def main():
    merged_json_file = Path(sys.argv[1])    
    pdfs_file = Path(sys.argv[2])
    wayback_json_file = Path(sys.argv[3])
    archive_json_file = Path(sys.argv[4])    

    upload_all_internet_archive(merged_json_file, pdfs_file, wayback_json_file, archive_json_file)

main()



"""
 {
    "SN": "1",
    "Department Name": "Agriculture, Dairy Development, Animal Husbandry and Fisheries Department",
    "Title": "Regarding approving the implementation of District Agricultural Festival Scheme in the year 2023-24..",
    "Unique Code": "202401101217404701",
    "G.R. Date": "10-01-2024",
    "File Size (KB)": "150",
    "Download": "https://gr.maharashtra.gov.in/Site/Upload/Government%20Resolutions/English/202401101217404701.pdf"
  },
"""
