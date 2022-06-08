# AmazonMQ - Broker reconfiguration utility
Serverless utility to reconfigure the NLB endpoint that is used as a facade to the ENI's connecting to Amazon MQ for RabbitMQ broker. It also includes a module to auto scale Amazon MQ broker based on aggregated CPU utilization. 

# Prerequisites
Install SAM cli by following the instructions provided in [documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html).

# Instructions
The entire utility is packaged as a Serverless Application Model (SAM) template.More details on SAM can be found [here](https://aws.amazon.com/serverless/sam/).


1.  Clone the amq-autoscaling-util project.
    ```bash
    git clone https://github.com/mithun008/amq-autoscaling-util.git
    ```
1. Go the amq-autoscaling-util folder.

1. Capture the ARN for the NLB that points to the broker ENI's.

1. Build the SAM template by running the below command.
    ```bash
    sam build
    ```
1. Deploy SAM template
    ```bash
    sam deploy --guided
    ```
    The command will prompt for the ARN of the NLB that points to the broker ENI's.

