$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if ((minikube status --format '{{.APIServer}}') -ne 'Running') {
    throw 'Minikube is not running. Start it with: minikube start --driver=docker --container-runtime=docker'
}

$runtime = kubectl get node minikube -o jsonpath='{.status.nodeInfo.containerRuntimeVersion}'
if ($runtime -notlike 'docker://*') {
    throw "Minikube must use the Docker runtime, found: $runtime. Recreate it: minikube delete; minikube start --driver=docker --container-runtime=docker"
}

$certLine = minikube docker-env --shell powershell | Select-String 'DOCKER_CERT_PATH'
$certPath = ($certLine.Line -split '"')[1]
$target = Join-Path $PSScriptRoot 'secrets/certs'
New-Item -ItemType Directory -Force -Path $target | Out-Null
foreach ($name in 'ca.pem', 'cert.pem', 'key.pem') {
    Copy-Item -Path (Join-Path $certPath $name) -Destination $target -Force
}

$config = kubectl config view --raw --minify --flatten --context minikube
$config = $config -replace 'server: https://\S+', 'server: https://minikube:8443'
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'secrets/kubeconfig'), (($config -join "`n") + "`n"))

$envFile = Join-Path $PSScriptRoot '.env'
if (-not (Test-Path $envFile)) {
    $chars = [char[]]((48..57) + (65..90) + (97..122))
    $password = -join (1..20 | ForEach-Object { $chars | Get-Random })
    [IO.File]::WriteAllText($envFile, "JENKINS_ADMIN_ID=admin`nJENKINS_ADMIN_PASSWORD=$password`n")
}

Write-Host 'Ready. Docker certificates and kubeconfig are in ci/jenkins/secrets, the Jenkins login is in ci/jenkins/.env'
