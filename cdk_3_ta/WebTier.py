import aws_cdk.core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_autoscaling as autos
import aws_cdk.aws_elasticloadbalancingv2 as elb




#this class encapsulates the CDK logic to build a Web Tier
class WebTierEC2:



    def __init__(self,stack: cdk.Stack,vpc: ec2.Vpc, hostType: str,
                    appDNS: str,webSecurityGroup: ec2.SecurityGroup,
                    albSecurityGroup:ec2.SecurityGroup) -> None:
  
        #We need to install Python 3.8 to support Flask
        ec2InitElement1 = ec2.InitPackage.yum(package_name="python38.x86_64") 
        #We need "stress" utility to simulate/test  high workload and trigger auto-scaling
        ec2InitElement2 = ec2.InitPackage.yum(package_name="stress")   
        
        #Web business logic (web.py) deployment from local resources
        ec2InitElement3 = ec2.InitFile.from_file_inline(  target_file_name="/home/ec2-user/web.py",
                                        source_file_name="ect-cdk-3ta-resources/web.py",
                                        mode="000644",
                                        group="ec2-user",
                                        owner="ec2-user")
        #log stream script (awslogs-agent-setup-py) config file  deployment from local resources
        ec2InitElement4 = ec2.InitFile.from_file_inline(  target_file_name="/tmp/cwlogs/my.conf",
                                        source_file_name="ect-cdk-3ta-resources/my.conf",
                                        mode="000644",
                                        group="root",
                                        owner="root")
        #log stream script (awslogs-agent-setup-py) deployment from local resources
        ec2InitElement5 = ec2.InitFile.from_file_inline(  target_file_name="/home/ec2-user/awslogs-agent-setup.py",
                                        source_file_name="ect-cdk-3ta-resources/awslogs-agent-setup.py",
                                        mode="000644",
                                        group="root",
                                        owner="root")

        #install required Python packages
        ec2InitElement6 = ec2.InitCommand.shell_command(shell_command="pip-3.8 install flask boto3 urllib3",cwd="/home/ec2-user/")
        
        #start Flask script
        flaskScriptcommand = f'python3 web.py "http://{appDNS}" > web.log 2>&1 &'
        #cdk.CfnOutput(stack, "flask-script-web",description="Flask script command", value=flaskScriptcommand)
        ec2InitElement7 = ec2.InitCommand.shell_command(shell_command=flaskScriptcommand,cwd="/home/ec2-user/")
      
        #start log stream agent script
        ec2InitElement8= ec2.InitCommand.shell_command(shell_command=f"python2.7 awslogs-agent-setup.py -n -r {stack.region} -c /tmp/cwlogs/my.conf &",cwd="/home/ec2-user/")
       
        
        #deploying sequence
        ec2Init = ec2.CloudFormationInit.from_elements( ec2InitElement1,
                                                        ec2InitElement2,
                                                        ec2InitElement3,
                                                        ec2InitElement4,
                                                        ec2InitElement5,
                                                        ec2InitElement6,
                                                        ec2InitElement7,
                                                        ec2InitElement8)
                                                            

        #define compute class type
        instanceType = ec2.InstanceType(instance_type_identifier=hostType)
        #using defaul AWS Linux Image
        machineImage = ec2.AmazonLinuxImage()
        #required permissions to allow SSM connectivity 
        iamSSMManagedPolicy = iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess")
        #required permissions to allow CloudWatch Logs publishing
        iamLogManagedPolicy = iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
        
        #Create Role for EC2 with attached permissions/policies
        instanceRole = iam.Role(stack,"Web EC2 Role",
                          assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                          managed_policies=[iamSSMManagedPolicy,iamLogManagedPolicy])


       
       
        #create Auto Scaling Group with all the information required to create an instance
        # and the group management
        autoScaling = autos.AutoScalingGroup(
                    stack,"WebApp",instance_type=instanceType,
                    machine_image=machineImage,
                    init=ec2Init,
                    signals=autos.Signals.wait_for_all(),
                    min_capacity=2,#min 2 EC2 needed
                    max_capacity=4,#max 4 EC2 running in case of workload increase
                    desired_capacity=2,#always keep two EC2 running (one per AZ)
                    vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
                    cooldown=cdk.Duration.seconds(120),
                    health_check=autos.HealthCheck.ec2(grace=cdk.Duration.seconds(120)),
                    vpc=vpc,
                    role=instanceRole,
                    security_group=webSecurityGroup)

        

        #Monitor group using CPU utilization, target is 40%, It will scale up or down to maintain this target
        autoScaling.scale_on_cpu_utilization("WebOnCPUUtilization",target_utilization_percent=40.0,
                                                cooldown=cdk.Duration.seconds(60),
                                                estimated_instance_warmup=cdk.Duration.seconds(120))

        #Create an Application Load Balancer (see https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html)
        alb = elb.ApplicationLoadBalancer(stack,"WebLoadBalancer",
                                    vpc=vpc,
                                    internet_facing=True,#public access
                                    security_group=albSecurityGroup)   
        #ALB is listening on HTTP:80 for incomining calls
        albListener = elb.ApplicationListener(stack,"WebELBListener",
                                port=80,
                                protocol= elb.ApplicationProtocol.HTTP,
                                load_balancer=alb,
                                open=True)
        #The Auto Scaling Group is the ALP's target and will forward request to HTTP:80
        albListener.add_targets("WebTarget",port=80,
                                      protocol=elb.ApplicationProtocol.HTTP,
                                      targets=[autoScaling])

        #print out public DNS entry point to use the stack
        cdk.CfnOutput(stack, "WebALBDNS",description="Public DNS entry point", value=alb.load_balancer_dns_name)
  
        

    