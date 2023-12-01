import unittest

from .context import workflow_handler as wh

import os
os.chdir("..")
os.chdir("..")


class testCase(unittest.TestCase):

    def test_get_samplesheet_samples(self):
        path = "temp/unittest_samplesheet.txt"
        # Note: all sample info used is fictional
        lines = ["[Data]\n",
                 "Sample_ID,Sample_Name,Sample_Plate,Sample_Well,Index_ID,index,index2,Sample_Type,Pair_ID\n",
                 "123456789-12345S1234-00TSOD00-8471,123456789-12345S1234-00TSOD00-8471,NV1234567-LIB,A0,UDP1234,AAAAAAAAAA,AAAAAAAAAA,DNA,123456789-12345S1234-00TSOD00-8471\n",
                 "123456789-12345S1235-00TSOD00-8471,123456789-12345S1235-00TSOD00-8471,NV1234567-LIB,A0,UDP1234,AAAAAAAAAA,AAAAAAAAAA,DNA,123456789-12345S1235-00TSOD00-8471\n",
                 "123456789-12345S1236-00TSOD00-8471,123456789-12345S1236-00TSOD00-8471,NV1234567-LIB,A0,UDP1234,AAAAAAAAAA,AAAAAAAAAA,DNA,123456789-12345S1236-00TSOD00-8471\n",
                 "123456789-12345S1237-00TSOD00-8471,123456789-12345S1237-00TSOD00-8471,NV1234567-LIB,A0,UDP1234,AAAAAAAAAA,AAAAAAAAAA,DNA,123456789-12345S1237-00TSOD00-8471\n"]
        with open(path, "w") as file:
            file.writelines(lines)
        sample_list = wh.get_samplesheet_samples(path)
        os.remove(path)
        assert len(sample_list) == 4


if __name__ == "__main__":
    unittest.main()
