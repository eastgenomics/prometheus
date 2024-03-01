from bin.annotation import get_clinvar_files as gc
import unittest
from unittest.mock import Mock, patch
import ftplib


class testGetClinvarFiles(unittest.TestCase):

    @patch("ftplib.FTP.login", Mock(return_value=None))
    @patch("ftplib.FTP.cwd", Mock(return_value=None))
    def test_connect_to_website(self):
        """test connect_to_website can connect to website
        """
        link = "https://ftp.ncbi.nlm.nih.gov"
        path = "/path/to/file"
        assert type(gc.connect_to_website(link, path, "b37")) is ftplib.FTP

    @patch("time.sleep")
    @patch("bin.annotation.get_clinvar_files.FTP.retrlines")
    @patch("bin.annotation.get_clinvar_files.connect_to_website")
    def test_get_ftp_files(self, mock_connect, mock_retr, mock_sleep):
        """test get_ftp_files can return latest clinvar vcf,
            index, date of most recent version, and version name
        """
        mock_connect.return_value.mock_retr.return_values = [
            'file1_240227.vcf.gz'
        ]
        base_vcf_link = "https://ftp.ncbi.nlm.nih.gov"
        base_vcf_path = "/path/to/file"
        genome_build = "b37"
        (
            recent_vcf_file, recent_tbi_file, latest_time,
            recent_vcf_version
        ) = gc.get_ftp_files(base_vcf_link, base_vcf_path, genome_build)
        with self.subTest():
            assert recent_vcf_file == "file1_240227.vcf.gz"
        with self.subTest():
            assert recent_tbi_file == "file1_240227.vcf.gz.tbi"
        with self.subTest():
            assert latest_time is not None
        with self.subTest():
            assert recent_vcf_version == "240227"


if __name__ == "__main__":
    unittest.main()
