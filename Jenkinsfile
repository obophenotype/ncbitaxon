pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'make'
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'ncbitaxon.*'
        }
    }
}
