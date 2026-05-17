pipeline {
    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-agent
spec:
  containers:
  - name: node
    image: node:20-alpine
    command:
    - cat
    tty: true
    resources:
      requests:
        memory: "512Mi"
        cpu: "250m"
      limits:
        memory: "1Gi"
        cpu: "500m"
    env:
    - name: DD_AGENT_HOST
      valueFrom:
        fieldRef:
          fieldPath: status.hostIP
'''
            defaultContainer 'node'
        }
    }

    environment {
        DD_ENV            = 'ci'
        DD_SERVICE        = 'datadog-demo-app'
        DD_VERSION        = "${env.BUILD_NUMBER}"
        DD_CIVISIBILITY_ENABLED            = 'true'
        DD_CIVISIBILITY_AGENTLESS_ENABLED  = 'false'
        DD_TRACE_CI_VISIBILITY_ENABLED     = 'true'
        DATADOG_API_KEY   = credentials('datadog-api-key')
        JEST_JUNIT_OUTPUT_DIR  = 'test-results'
        JEST_JUNIT_OUTPUT_NAME = 'results.xml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                dir('datadog-demo-app') {
                    sh 'npm ci'
                }
            }
        }

        stage('Lint') {
            steps {
                dir('datadog-demo-app') {
                    sh 'npm run lint || true'
                }
            }
        }

        stage('Test') {
            steps {
                dir('datadog-demo-app') {
                    sh '''
                        mkdir -p test-results
                        npx jest \
                          --reporters=default \
                          --reporters=jest-junit \
                          --forceExit \
                          2>&1 | tee test-output.log || true
                    '''
                }
            }
            post {
                always {
                    junit(
                        testResults: 'datadog-demo-app/test-results/results.xml',
                        allowEmptyResults: true
                    )
                }
            }
        }

        stage('Upload Test Results to Datadog') {
            steps {
                dir('datadog-demo-app') {
                    sh '''
                        export DD_API_KEY=$DATADOG_API_KEY
                        npx @datadog/datadog-ci junit upload \
                          --service datadog-demo-app \
                          --env ci \
                          test-results/results.xml || true
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'datadog-demo-app/test-output.log',
                allowEmptyArchive: true
            )
        }
        success {
            echo "Pipeline succeeded - CI Visibility data sent to Datadog"
        }
        failure {
            echo "Pipeline failed - check Datadog CI for flaky test details"
        }
    }
}
