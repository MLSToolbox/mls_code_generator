# MLSToolbox Code Generator

[![Python Tests and Coverage](https://github.com/MLSToolbox/mls_code_generator/actions/workflows/main.yml/badge.svg)](https://github.com/MLSToolbox/mls_code_generator/actions/workflows/main.yml)
[![codecov](https://codecov.io/github/MLSToolbox/mls_code_generator/graph/badge.svg)](https://codecov.io/github/MLSToolbox/mls_code_generator)

MLSToolbox Code Generator is a user-friendly, extensible, and comprehensive tool designed to support data scientists in automating the creation of high-quality ML pipelines based on the application of the core software engineering design principles (cohesion, coupling and object-oriented SOLID principles).

## Documentation
You can find all the information you need in our [WIKI!](https://github.com/MLSToolbox/mls_code_generator/wiki).

# Demos
This video shows how to use the MLSToolbox Pipeline Code generator to define a pipeline and generate the code to create the ML model. More details about the example used in this video are available at [mls_code_generator Wiki](https://github.com/MLSToolbox/mls_code_generator/wiki/Diabetes-prediction).

https://github.com/user-attachments/assets/5c783523-529b-4cee-a7e6-7fc400e53633

You can find more videos at [mls_code_generator Wiki](https://github.com/MLSToolbox/mls_code_generator/wiki/Videos).

## Deployment
```bash
docker build -t server_mls .
docker run -d -p 5000:5000 server_mls
```
