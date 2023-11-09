#!/bin/bash
### contents of setoff_reports_workflow.sh
WORKFLOW_ID=$1
PROJECT_ID=$2
VERSION_NUMBER=$3

# Select project
dx select $PROJECT_ID

# Location of Helios folder
HELIOS_FOLDER=$(dx ls $PROJECT_ID:/$VERSION_NUMBER/output/)

# Setting output path variables
OUTPUT_PATH=$VERSION_NUMBER/output/$HELIOS_FOLDER
OUTPUT_PATH1=$VERSION_NUMBER/output/testing_output

# Setting sample list variable
SAMPLE_LIST=$(dx find data --json --name "*_SampleAnalysisResults.json" --path $PROJECT_ID | jq -r '.[].describe.name')
SAMPLE_LIST=$(sed s'/_SampleAnalysisResults.json//g' <<< $SAMPLE_LIST)
echo $SAMPLE_LIST

# Run test
for SAMPLE_PREFIX in $SAMPLE_LIST; do
    isBAMdna=$(dx find data --name "${SAMPLE_PREFIX}*.bam" --path $PROJECT_ID:${OUTPUT_PATH}/eggd_tso500/analysis_folder/Logs_Intermediates/StitchedRealigned/ --brief)

    if [[ $isBAMdna ]]; then

        dx run $WORKFLOW_ID \
            $(dx find data --name "${SAMPLE_PREFIX}*.fastq.gz" --path $PROJECT_ID:${OUTPUT_PATH}/eggd_tso500/analysis_folder/Logs_Intermediates/FastqGeneration/ --brief | sed 's/^/-istage-GFQZjB84b0bxz4Yg1y3ygKJZ.fastqs=/') \
            -istage-GF22j384b0bpYgYB5fjkk34X.bam=$(dx find data --name "${SAMPLE_PREFIX}*.bam" --path $PROJECT_ID:${OUTPUT_PATH}/eggd_tso500/analysis_folder/Logs_Intermediates/StitchedRealigned/ --brief) \
            -istage-GF22j384b0bpYgYB5fjkk34X.index=$(dx find data --name "${SAMPLE_PREFIX}*.bai" --path $PROJECT_ID:${OUTPUT_PATH}/eggd_tso500/analysis_folder/Logs_Intermediates/StitchedRealigned/ --brief) \
            -istage-GF22GJQ4b0bjFFxG4pbgFy5V.name=${SAMPLE_PREFIX} \
            -istage-GF25f384b0bVZkJ2P46f79xy.gvcf=$(dx find data --name "${SAMPLE_PREFIX}*.genome.vcf" --path $PROJECT_ID:${OUTPUT_PATH}/eggd_tso500/analysis_folder/Results/ --brief) \
            --name $(dx describe $WORKFLOW_ID --name)_${SAMPLE_PREFIX} \
            --destination="$PROJECT_ID/${OUTPUT_PATH1}/$(dx describe --json $WORKFLOW_ID | jq -r '.name')" -y
    else
    echo "RNA sample"
    fi
done