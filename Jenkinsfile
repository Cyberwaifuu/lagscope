pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        IMAGE = 'lagscope'
        K8S_NAMESPACE = 'lagscope'
    }

    stages {
        stage('Prepare') {
            steps {
                script {
                    env.SHORT_SHA = sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()
                    env.TEST_CONTAINER = "lagscope-test-${env.BUILD_NUMBER}-${env.SHORT_SHA}"
                    env.SMOKE_CONTAINER = "lagscope-smoke-${env.BUILD_NUMBER}-${env.SHORT_SHA}"
                }
                sh 'docker version'
            }
        }

        stage('Build test image') {
            steps {
                sh 'docker build --target test -t "$IMAGE:test-$SHORT_SHA" .'
            }
        }

        stage('Lint') {
            steps {
                sh 'docker run --rm "$IMAGE:test-$SHORT_SHA" sh -c "ruff check . && ruff format --check ."'
            }
        }

        stage('Unit tests') {
            steps {
                sh '''
                    docker run --name "$TEST_CONTAINER" "$IMAGE:test-$SHORT_SHA" sh -c \
                        "python scripts/make_synthetic.py --check && pytest --junitxml=reports/junit.xml --cov --cov-report=term --cov-fail-under=90"
                '''
            }
            post {
                always {
                    sh '''
                        rm -rf reports
                        docker cp "$TEST_CONTAINER:/app/reports" reports || true
                        docker rm -f "$TEST_CONTAINER" || true
                    '''
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                }
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build --target runtime --label "org.opencontainers.image.revision=$GIT_COMMIT" -t "$IMAGE:$SHORT_SHA" .'
                sh 'docker image ls "$IMAGE:$SHORT_SHA"'
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                    docker run -d --name "$SMOKE_CONTAINER" "$IMAGE:$SHORT_SHA"
                    for attempt in $(seq 1 30); do
                        status=$(docker inspect --format '{{.State.Health.Status}}' "$SMOKE_CONTAINER")
                        echo "attempt $attempt: $status"
                        [ "$status" = healthy ] && exit 0
                        [ "$status" = unhealthy ] && exit 1
                        sleep 3
                    done
                    exit 1
                '''
            }
            post {
                always {
                    sh 'docker rm -f "$SMOKE_CONTAINER" || true'
                }
            }
        }

        stage('Deploy to Minikube') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    sed "s|lagscope:IMAGE_TAG|$IMAGE:$SHORT_SHA|" k8s/lagscope.yaml | kubectl apply -f -
                    kubectl -n "$K8S_NAMESPACE" rollout status deployment/lagscope --timeout=180s
                    kubectl -n "$K8S_NAMESPACE" get deployment,pods,service -o wide
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker image rm "$IMAGE:test-$SHORT_SHA" || true
                docker image prune -f || true
            '''
        }
    }
}
