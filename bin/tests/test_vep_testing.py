import unittest

from .context import vep_testing as vt

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_get_diff_output(self):
        dev_content = ["1:2488153:A:G 135349 not_provided .",
                       "1:11181327:C:T 516652 Benign .",
                       "1:11188164:G:A 584432 Pathogenic .",
                       "1:11190646:G:A 380311 Likely_Benign ."]

        prod_content = ["1:2488153:A:G 135349 not_provided .",
                        "1:11181327:C:T 516652 Likely_Benign .",
                        "1:11188164:G:A 584432 Pathogenic .",
                        "1:11190646:G:A 380311 Benign ."]

        with open("test_dev.txt", "w") as f:
            f.writelines(dev_content)
            f.write("\n")
        with open("test_prod.txt", "w") as f:
            f.writelines(prod_content)
            f.write("\n")

        output = "temp/tso500_diff_output.txt"

        assert vt.get_diff_output("test_dev.txt",
                                  "test_prod.txt",
                                  "tso500", "bin") == output
        os.remove(output)
        os.remove("test_dev.txt")
        os.remove("test_prod.txt")


if __name__ == "__main__":
    unittest.main()
