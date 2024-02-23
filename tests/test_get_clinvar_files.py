from bin.annotation import get_clinvar_files as gc, get_ftp_files
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

    def test_get_ftp_files(self):
        """test get_ftp_files can return latest clinvar vcf,
            index, date of most recent version, and version name
        """
        base_vcf_link = "https://ftp.ncbi.nlm.nih.gov"
        base_vcf_path = "/path/to/file"
        genome_build = "b37"
        with patch("bin.annotation.get_clinvar_files.connect_to_website") as mock_connect:
            mock_connect.return_value = None
            (
                recent_vcf_file, recent_tbi_file, latest_time,
                recent_vcf_version
            ) = get_ftp_files(base_vcf_link, base_vcf_path, genome_build)
        assert (
            recent_vcf_file is not None
            and recent_tbi_file is not None
            and latest_time is not None
            and recent_vcf_version is not None
        )

    def test_get_ftp_files_2(self):
        with patch("bin.annotation.get_clinvar_files.connect_to_website") as mock_connect:
            mock_connect.return_value = None
            expected_error = "Error: invalid base vcf link provided to connect_to_website"
            with self.assertRaisesRegex(RuntimeError, expected_error):
                get_ftp_files("dev", "null", "nothing")


if __name__ == "__main__":
    unittest.main()
