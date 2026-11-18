"""Package the standalone editor, current backup, generated codes, and user guide."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
FILES=['FOF_Profile_Studio_v3_11.html','FOF_Profile_Backup_All_Faculty_2026-11-18.json',
       'FOF_Profile_Codes_All_Faculty_2026-11-18.zip','STUDIO_V3_11.md']
def main():
    for file in FILES:assert (ROOT/file).is_file(),file
    output=ROOT/'FOF_Profile_Studio_v3_11_Package_2026-11-18.zip'
    with ZipFile(output,'w',ZIP_DEFLATED) as archive:
        for file in FILES:archive.write(ROOT/file,file)
        assert archive.testzip() is None
    print(output.name,output.stat().st_size)
if __name__=='__main__':main()
