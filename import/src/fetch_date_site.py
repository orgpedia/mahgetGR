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
        if len(cells) != 1:
            import pdb

            pdb.set_trace()
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
        #crawler.save_screenshot(output_dir / f"{abbr}-{start_idx}.png")
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
            print('Next page not found on Page Number: {start_idx}+')
            break
        crawler.wait(4)
    print(f"Done crawling: {abbr}")


GovResolutionsURL = "https://gr.maharashtra.gov.in/1145/Government-Resolutions"
if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {sys.argv[0]} <website_dir> [<start_date> <end_date>]")
        sys.exit(1)

    today = datetime.date.today()
    months = "-jan-feb-mar-apr-may-jun-jul-aug-sep-oct-nov-dec".split("-")
    month_dir = months[today.month].capitalize()

    website_dir = Path(sys.argv[1]) / f'{month_dir}-{today.year}'
    website_dir.mkdir(exist_ok=True)

    if len(sys.argv) > 2:
        start_date = parse_date(sys.argv[2])
        to_date = parse_date(sys.argv[3])
    else:
        to_date = today
        start_date = to_date - datetime.timedelta(days=3)

    date_str = get_date_str(today)

    existing_dirs = list(website_dir.glob(f"{date_str}*"))
    output_dir = website_dir / f"{date_str}_v{len(existing_dirs)+1}"
    output_dir.mkdir(exist_ok=False)

    crawler = trav.start(GovResolutionsURL, output_dir / "logs.txt")
    fetch_site(crawler, start_date, to_date, output_dir)
