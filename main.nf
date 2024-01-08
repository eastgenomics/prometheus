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
        path config_path
        path cred_path

    output:
        val genomeBuild

    script:
        
        """
        python3 ${pathToBin}/annotation_update.py ${pathToBin} ${genomeBuild} ${config_path} ${cred_path}
        """
}

process updateVepConfigs
{
    input:
        each genomeBuild
        val assay
        path config_path
        path cred_path

    output:
        val assay

    script:
        
        """
        python3 ${pathToBin}/vep_config_update.py ${pathToBin} ${assay} ${genomeBuild} ${config_path} ${cred_path}
        """
}

process updateReportsWorkflow
{
    input:
        each genomeBuild
        val assay
        path config_path
        path cred_path

    script:
        
        """
        python3 ${pathToBin}/reports_workflow_update.py ${pathToBin} ${genomeBuild} ${config_path} ${cred_path}
        """
}

workflow 
{
    // run prometheus
    // update clinvar annotation resource files
    // b37 and b38 in parallel
    // genomes = Channel.of("b37", "b38")
    genomes = Channel.of("b37")
    annotation = getClinvarFiles(genomes, params.config_path, params.cred_path)

    // update vep config files per assay
    // TSO500, TWE, CEN, and MYE in parallel
    assays = Channel.of("TSO500", "TWE", "CEN")
    vep = updateVepConfigs(annotation, assays, params.config_path, params.cred_path)

    // update TSO500 reports workflow
    updateReportsWorkflow(genomes, vep.filter {it == "TSO500"}, params.config_path, params.cred_path)
}
