#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ "$(minikube status --format '{{.APIServer}}' || true)" != "Running" ]; then
    echo "Minikube is not running. Start it with: minikube start --driver=docker --container-runtime=docker" >&2
    exit 1
fi

runtime=$(kubectl get node minikube -o jsonpath='{.status.nodeInfo.containerRuntimeVersion}')
case "$runtime" in
    docker://*) ;;
    *)
        echo "Minikube must use the Docker runtime, found: $runtime" >&2
        exit 1
        ;;
esac

cert_path=$(minikube docker-env --shell bash | sed -n 's/^export DOCKER_CERT_PATH="\(.*\)"$/\1/p')
mkdir -p secrets/certs
for name in ca.pem cert.pem key.pem; do
    cp "$cert_path/$name" secrets/certs/
done

kubectl config view --raw --minify --flatten --context minikube \
    | sed -E 's#server: https://[^[:space:]]+#server: https://minikube:8443#' > secrets/kubeconfig

if [ ! -f .env ]; then
    password=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 20 || true)
    printf 'JENKINS_ADMIN_ID=admin\nJENKINS_ADMIN_PASSWORD=%s\n' "$password" > .env
fi

echo "Ready. Docker certificates and kubeconfig are in ci/jenkins/secrets, the Jenkins login is in ci/jenkins/.env"
