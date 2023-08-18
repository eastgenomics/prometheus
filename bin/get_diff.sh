#!/bin/bash
# takes the diff of two input files (input_file_1 and input_file_2)
# returns a text file containing the output of the bash command "diff"
# inputs: input_file_1 (string), input_file_2 (string)
# output: output_file

input_file_1=$1
input_file_2=$2
output_file=$3
diff --suppress-common-lines ${input_file_1} ${input_file_2} > ${output_file}
