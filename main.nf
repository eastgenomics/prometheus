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
        python ${pathToBin}/main.py
        """
}

workflow 
{
    // run prometheus
    getClinvarFiles()
}