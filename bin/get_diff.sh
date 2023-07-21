#!/bin/bash

input_file_1=$1
input_file_2=$2
output_file=$3
diff --suppress-common-lines ${input_file_1} ${input_file_2} > ${output_file}
