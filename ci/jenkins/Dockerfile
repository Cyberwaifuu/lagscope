FROM jenkins/jenkins:lts-jdk21

USER root

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG KUBECTL_VERSION=v1.37.1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN arch="$(dpkg --print-architecture)" && \
    curl -fsSLo /tmp/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${arch}/kubectl" && \
    curl -fsSLo /tmp/kubectl.sha256 "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${arch}/kubectl.sha256" && \
    echo "$(cat /tmp/kubectl.sha256)  /tmp/kubectl" | sha256sum --check && \
    install -m 0755 /tmp/kubectl /usr/local/bin/kubectl && \
    rm /tmp/kubectl /tmp/kubectl.sha256

USER jenkins

RUN jenkins-plugin-cli --plugins configuration-as-code job-dsl workflow-aggregator git junit pipeline-stage-view timestamper

COPY --chown=jenkins:jenkins casc.yaml /usr/share/jenkins/casc.yaml
