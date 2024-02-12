import json
import sys
from pathlib import Path

json_file = Path(sys.argv[1])

infos = json.loads(json_file.read_text())

d = {i["Unique Code"]: i for i in infos}

json_file.write_text(json.dumps(list(d.values())))
