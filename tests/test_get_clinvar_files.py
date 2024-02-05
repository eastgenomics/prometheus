from bin.annotation import get_clinvar_files as gc
import unittest
from unittest.mock import Mock, patch
import ftplib
import re


class testGetClinvarFiles(unittest.TestCase):

    @patch("ftplib.FTP.login", Mock(return_value=None))
    @patch("ftplib.FTP.cwd", Mock(return_value=None))
    def test_connect_to_website(self):
        """test connect_to_website can connect to website
        """
        assert type(gc.connect_to_website("", "b37")) is ftplib.FTP

    @patch(
        "bin.annotation.get_clinvar_files.connect_to_website",
        Mock(return_value=None)
    )
    def test_get_ftp_files(self):
        """test get_ftp_files returns valid file names
        """
        # TODO: patch over ftp.retrlines call
        (
            recent_vcf_file,
            recent_tbi_file,
            latest_time,
            recent_vcf_version
        ) = gc.get_ftp_files("", "b37")

        assert (
            re.match(r".+.vcf.gz", recent_vcf_file)
            and re.match(r".+.vcf.gz.tbi", recent_tbi_file)
            and re.match(r"^\d{8}$", recent_vcf_version)
        )


if __name__ == "__main__":
    unittest.main()
