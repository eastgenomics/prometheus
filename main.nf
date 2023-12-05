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
    input:
        val genomeBuild

    output:
        val genomeBuild

    script:
        
        """
        python ${pathToBin}/annotation_update.py ${pathToBin} ${genomeBuild}
        """
}

process updateVepConfigs
{
    input:
        val assay
        val genomeBuild

    output:
        val assay

    script:
        
        """
        python ${pathToBin}/vep_config_update.py ${pathToBin} ${assay} ${genomeBuild}
        """
}

process updateReportsWorkflow
{
    input:
        val genomeBuild

    script:
        
        """
        python ${pathToBin}/reports_workflow_update.py ${pathToBin} ${genomeBuild}
        """
}

workflow 
{
    // run prometheus
    // update clinvar annotation resource files
    // b37 and b38 in parallel
    genomes = Channel.of("b37", "b38")
    annotation = getClinvarFiles(genomes)

    // update vep config files per assay
    // TSO500, TWE, CEN, and MYE in parallel
    assays = Channel.of("TSO500", "TWE", "CEN")
    vep = updateVepConfigs(annotation, assays)

    // update TSO500 reports workflow
    updateReportsWorkflow(vep.filter {it == "TSO500"})
}