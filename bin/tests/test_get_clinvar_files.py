from .context import get_clinvar_files as gc
import unittest
from unittest.mock import Mock
import ftplib
import re
import os

os.chdir("..")
os.chdir("..")


class testGetClinvarFiles(unittest.TestCase):

    def test_connect_to_website(self):
        """test connect_to_website can connect to website
        """
        assert type(gc.connect_to_website()) is ftplib.FTP

    def test_get_ftp_files(self):
        """test get_ftp_files returns valid file names
        """
        (
            recent_vcf_file,
            recent_tbi_file,
            latest_time,
            recent_vcf_version
        ) = gc.get_ftp_files()

        assert (
            re.match(r".+.vcf.gz", recent_vcf_file)
            and re.match(r".+.vcf.gz.tbi", recent_tbi_file)
            and re.match(r"^\d{8}$", recent_vcf_version)
        )


if __name__ == "__main__":
    unittest.main()
