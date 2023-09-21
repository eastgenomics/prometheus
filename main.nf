nextflow.enable.dsl=2

if (params.run_type == "local") {
    print("This workflow is running locally!")
    pathToBin = "$projectDir/bin"
    pathToInput = "$projectDir/input"
    pathToProjectDir = "$projectDir"
}
else {
    pathToBin = "nextflow-bin"
    pathToInput = "input"
    pathToProjectDir = ""
}

process getClinvarFiles
{
    script:
        
        """
        python ${pathToBin}/annotation_update.py
        """
}

process updateVepConfigs
{
    script:
        
        """
        python ${pathToBin}/vep_config_update.py
        """
}

workflow 
{
    // run prometheus
    // update clinvar annotation resource files
    // b37 and b38 in parallel
    getClinvarFiles()

    // update vep config files per assay
    // TSO500, TWE, CEN, and MYE in parallel
    updateVepConfigs()
}