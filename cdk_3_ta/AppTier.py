from aws_cdk.aws_rds import DatabaseSecret
import aws_cdk.core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_autoscaling as autos
import aws_cdk.aws_elasticloadbalancingv2 as elb





class AppTierEC2:



    
   

    def __init__(self,stack: cdk.Stack,vpc: ec2.Vpc, hostType: str,
                dbAccessSecretName: str,appSecurityGroup: ec2.SecurityGroup,
                albSecurityGroup: ec2.SecurityGroup) -> None:
  
                
        ec2InitElement1 = ec2.InitPackage.yum(package_name="python38.x86_64") 
        ec2InitElement2 = ec2.InitPackage.yum(package_name="stress")   
        ec2InitElement3 = ec2.InitPackage.yum(package_name="mysql") 
    
        ec2InitElement4 = ec2.InitFile.from_file_inline(  target_file_name="/home/ec2-user/querydb.py",
                                        source_file_name="ect-cdk-3ta-resources/querydb.py",
                                        mode="000644",
                                        group="ec2-user",
                                        owner="ec2-user")

        ec2InitElement5 = ec2.InitFile.from_file_inline(  target_file_name="/tmp/cwlogs/my.conf",
                                        source_file_name="ect-cdk-3ta-resources/my.conf",
                                        mode="000644",
                                        group="root",
                                        owner="root")

        ec2InitElement6 = ec2.InitFile.from_file_inline(  target_file_name="/home/ec2-user/awslogs-agent-setup.py",
                                            source_file_name="ect-cdk-3ta-resources/awslogs-agent-setup.py",
                                            mode="000644",
                                            group="root",
                                            owner="root")

        

        ec2InitElement7 = ec2.InitCommand.shell_command(shell_command="pip-3.8 install flask boto3 pymysql",cwd="/home/ec2-user/")
        flaskScriptcommand = f'python3 querydb.py "{dbAccessSecretName}" "{stack.region}" > querydb.log 2>&1 &'
        cdk.CfnOutput(stack, "flask-script-app",description="Flask script command", value=flaskScriptcommand)
        ec2InitElement8 = ec2.InitCommand.shell_command(shell_command=flaskScriptcommand,cwd="/home/ec2-user/")
      
        ec2InitElement9= ec2.InitCommand.shell_command(shell_command=f"python2.7 awslogs-agent-setup.py -n -r {stack.region} -c /tmp/cwlogs/my.conf &",cwd="/home/ec2-user/")
       
        

        ec2Init = ec2.CloudFormationInit.from_elements( ec2InitElement1,
                                                        ec2InitElement2,
                                                        ec2InitElement3,
                                                        ec2InitElement4,
                                                        ec2InitElement5,
                                                        ec2InitElement6,
                                                        ec2InitElement7,
                                                        ec2InitElement8,
                                                        ec2InitElement9)
                                                           
                                                            

       


        instanceType = ec2.InstanceType(instance_type_identifier=hostType)
        machineImage = ec2.AmazonLinuxImage()

        iamSSMManagedPolicy = iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess")
        iamLogManagedPolicy = iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
        iamSecretManagedPolicy = iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")


        instanceRole = iam.Role(stack,"App EC2 Role",
                          assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                          managed_policies=[iamSSMManagedPolicy,iamLogManagedPolicy,iamSecretManagedPolicy])

        
        
       
        autoScaling = autos.AutoScalingGroup(
                    stack,"App",instance_type=instanceType,
                    machine_image=machineImage,
                    init=ec2Init,
                    signals=autos.Signals.wait_for_all(),
                    min_capacity=1,max_capacity=4,
                    desired_capacity=1,
                    vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
                    cooldown=cdk.Duration.seconds(120),
                    health_check=autos.HealthCheck.ec2(grace=cdk.Duration.seconds(120)),
                    vpc=vpc,
                    role=instanceRole,
                    security_group=appSecurityGroup)

     
        

        autoScaling.scale_on_cpu_utilization("AppOnCPUUtilization",target_utilization_percent=40.0,
                                                cooldown=cdk.Duration.seconds(60),
                                                estimated_instance_warmup=cdk.Duration.seconds(120))

        alb = elb.ApplicationLoadBalancer(stack,"AppLoadBalancer",
                                    vpc=vpc,
                                    internet_facing=False,
                                    security_group=albSecurityGroup)   
        
        albListener = elb.ApplicationListener(stack,"AppELBListener",
                                port=80,
                                protocol= elb.ApplicationProtocol.HTTP,
                                load_balancer=alb,
                                open=False)

        albListener.add_targets("AppTarget",port=80,
                                      protocol=elb.ApplicationProtocol.HTTP,
                                      targets=[autoScaling])

        self.__dns = alb.load_balancer_dns_name

       
        

    def getLoadBalancerDNS(self):
        return self.__dns
