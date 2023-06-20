#!/bin/bash

input_file=$1
prod_or_dev=$2
input_basename=$( basename $input_file )
file_name="${input_basename%_markdup_recalibrated_Haplotyper_annotated.vcf}"
bcftools +split-vep $input_file -f '%CHROM:%POS:%REF:%ALT %ClinVar %ClinVar_CLNSIG %ClinVar_CLNSIGCONF\n' -d | uniq > ${file_name}.${prod_or_dev}.txt
