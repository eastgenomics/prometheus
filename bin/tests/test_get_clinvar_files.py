from .context import get_clinvar_files as gc
import unittest

import ftplib
import re
import time
import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_connect_to_website(self):
        # safety feature to prevent too many requests to server
        time.sleep(1)
        assert type(gc.connect_to_website()) is ftplib.FTP

    def test_get_ftp_files(self):
        # safety feature to prevent too many requests to server
        time.sleep(1)
        (recent_vcf_file,
         recent_tbi_file,
         latest_time,
         recent_vcf_version) = gc.get_ftp_files()

        assert re.match(r".+.vcf.gz", recent_vcf_file)
        assert re.match(r".+.vcf.gz.tbi", recent_tbi_file)
        assert re.match(r"^\d{8}$", recent_vcf_version)


if __name__ == "__main__":
    unittest.main()
