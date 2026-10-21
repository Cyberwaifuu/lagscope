# Changelog

## Unreleased

- Multi-stage Dockerfile: a test image with the development tools and a slim runtime image for the Streamlit app, running as a non-root user with a health check.
- Jenkins pipeline (Jenkinsfile): lint, unit tests with a JUnit report, image build and a smoke test for every branch; branch main is deployed to Minikube.
- Jenkins configured as code in ci/jenkins (Docker image, Configuration as Code, Docker Compose) and Kubernetes manifests in k8s/.

## v0.1.0

- CSV loading with fourteen validation rules and plain-language error messages.
- Lag search over a common sample with AIC, BIC or HQIC.
- OLS estimation with classical or Newey–West (HAC) standard errors.
- Optional ADF, Granger and Ljung–Box diagnostics.
- Coefficient table, chart of the three series, CSV and PNG export.
- Streamlit interface with a synthetic example.
- CI on Ubuntu and Windows (Python 3.12, 3.13, 3.14), coverage gate at 90%, package build; release workflow on tags.
- Interface shows the value of the selected criterion, the five best lag pairs and p-values shortened for display (the CSV export keeps full precision).
