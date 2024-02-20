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
        assert type(gc.connect_to_website("", "b37")) is ftplib.FTP


if __name__ == "__main__":
    unittest.main()
