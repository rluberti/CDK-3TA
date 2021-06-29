
from cdk_3_ta.WebTier import WebTierEC2
from cdk_3_ta.AppTier import AppTierEC2
from cdk_3_ta.DataTier import MySQLRDS
import aws_cdk.core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_logs as log
import aws_cdk.aws_codedeploy as codedeploy






class Cdk3TaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
        #codedeploy.AutoRollbackConfig(failed_deployment=False)
        
        #VPC IPv4 range definition
        VPCCidrIp = "10.0.0.0/16"
       
        #We need a public (internet accessible) network subnet (Web Load Balancer will use it)
        publicSubnet = ec2.SubnetConfiguration(
                                        subnet_type = ec2.SubnetType.PUBLIC,
                                        name = "PUBLIC",
                                        cidr_mask = 24)
        #We need a private network subnet (EC2 and RDS will use it)  
        #PRIVATE will subnet will allow outbound traffic to internet
        privateSubnet =  ec2.SubnetConfiguration(
                                        subnet_type =  ec2.SubnetType.PRIVATE,
                                        name = "PRIVATE",
                                        cidr_mask = 24)
        #Create VPC
        myVpc = ec2.Vpc(self, "CDK-3TA", cidr=VPCCidrIp, max_azs=2,
                        nat_gateways=2,#automatically associated with PRIVATE subnets (one per subnet)
                        subnet_configuration = [publicSubnet,privateSubnet])
        #Create Log Group for VPC Flow Logs
        logGroupFlow =  log.LogGroup(self,'CDK-3TA-VPC-FLOWLOG-GROUP',
                                    log_group_name='CDK-3TA-VPC-FLOWLOG-GROUP',
                                    retention=log.RetentionDays.ONE_DAY,
                                    removal_policy=cdk.RemovalPolicy.DESTROY)
        
        #create Flow Logs, usefull to monitor network traffica
        myVpc.add_flow_log('CDK-3TA-FLOWLOG', destination = ec2.FlowLogDestination.to_cloud_watch_logs(logGroupFlow))

        #Create Log Group for EC2 (Web and App) custom log streams
        logEC2Group =  log.LogGroup(self,'CDK-3TA-EC2-LOG-GROUP',
                                    log_group_name='CDK-3TA-EC2-LOG-GROUP',
                                    retention=log.RetentionDays.ONE_DAY,
                                    removal_policy=cdk.RemovalPolicy.DESTROY)
        #Create metric to apply to custom logs
        #Logs will be published via the "awslogs-agent-setup.py" script installed in each EC2 instance
        log.MetricFilter(self, "CDK-3TA-EC2-LOG-GROUP-METRIC-FILTER",
                        log_group=logEC2Group,
                        metric_namespace="general/lines",
                        metric_name="flask1",
                        filter_pattern=log.FilterPattern.all_events(),
                        metric_value="1")

        #Create Security Group for Web Load Balancer and allow inbound HTTP:80 traffic from Internet. Any outbound traffic is allowed  
        webALBSecurityGroup = ec2.SecurityGroup(self,"WEB-ALB-SG",vpc=myVpc,allow_all_outbound=True)
        webALBSecurityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), connection=ec2.Port.tcp(80))      

        #Create Security Group for Web EC2 and allow inbound HTTP:80 traffic from Web Load Balancer only. Any outbound traffic is allowed  
        webSecurityGroup = ec2.SecurityGroup(self,"WEB-SG",vpc=myVpc,allow_all_outbound=True)
        webSecurityGroup.add_ingress_rule(webALBSecurityGroup,connection=ec2.Port.tcp(80))

        #Create Security Group for App Load Balancer and allow inbound HTTP:80 traffic from Web EC2 only. Any outbound traffic is allowed  
        appALBSecurityGroup = ec2.SecurityGroup(self,"APP-ALB-SG",vpc=myVpc,allow_all_outbound=True)
        appALBSecurityGroup.add_ingress_rule(webSecurityGroup,connection=ec2.Port.tcp(80))      

        #Create Security Group for App EC2 and allow inbound HTTP:80 traffic from App Load Balancer only. Any outbound traffic is allowed  
        appSecurityGroup = ec2.SecurityGroup(self,"APP-SG",vpc=myVpc,allow_all_outbound=True)
        appSecurityGroup.add_ingress_rule(appALBSecurityGroup,connection=ec2.Port.tcp(80)) 

        #Create Security Group for RDS and allow inbound HTTP:80 traffic from App EC2 only. Any outbound traffic is allowed  
        rdsSecurityGroup = ec2.SecurityGroup(self,"RDS-SG",vpc=myVpc,allow_all_outbound=True)
        rdsSecurityGroup.add_ingress_rule(appSecurityGroup,connection=ec2.Port.tcp(3306)) 

        
        #Create a MySQL RDS tier, code encapsulated into DataTier.py
        dbTierRDS = MySQLRDS(   stack=self,vpc=myVpc,
                                hostType="t2.micro",#min compute class type
                                dbName="db3ta",
                                dbGbSize=5,#min required size
                                securityGroup=rdsSecurityGroup)

        #return Secret Name to share with App tier in order to get DB credentials via AWS Secret Manager
        dbAccessSecretName = dbTierRDS.getSecretName()

        #Create App tier, code encapsulated into AppTier.py
        appTierEC2 = AppTierEC2(stack=self,vpc=myVpc,
                                hostType="t2.micro",#min compute class type
                                dbAccessSecretName=dbAccessSecretName,
                                appSecurityGroup=appSecurityGroup,
                                albSecurityGroup=appALBSecurityGroup)

        #return App Load Balancer DNS to pass to Web EC2 tier
        appELBDNS = appTierEC2.getLoadBalancerDNS()

        #Create Web tier, code encapsulated into WebTier.py
        WebTierEC2( stack=self,vpc=myVpc,
                    hostType="t2.micro",
                    appDNS=appELBDNS,
                    webSecurityGroup=webSecurityGroup,
                    albSecurityGroup=webALBSecurityGroup)




        
        

       





