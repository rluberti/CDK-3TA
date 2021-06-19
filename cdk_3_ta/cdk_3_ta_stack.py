
from WebTier import WebTierEC2
from AppTier import AppTierEC2
from DataTier import MySQLRDS
import aws_cdk.core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_logs as log


class Cdk3TaStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        
    
        

        VPCCidrIp = "10.0.0.0/16"
       
        
        publicSubnet = ec2.SubnetConfiguration(
                                        subnet_type = ec2.SubnetType.PUBLIC,
                                        name = "PUBLIC",
                                        cidr_mask = 24)
        
        privateSubnet =  ec2.SubnetConfiguration(
                                        subnet_type =  ec2.SubnetType.PRIVATE,
                                        name = "PRIVATE",
                                        cidr_mask = 24)
            
        myVpc = ec2.Vpc(self, "CDK-3TA", cidr=VPCCidrIp, max_azs=2,
                        nat_gateways=2,#automatically associated with PRIVATE subnets
                        subnet_configuration = [publicSubnet,privateSubnet])
       
        logGroupFlow =  log.LogGroup(self,'CDK-3TA-VPC-FLOWLOG-GROUP',
                                    log_group_name='CDK-3TA-VPC-FLOWLOG-GROUP',
                                    retention=log.RetentionDays.ONE_DAY,
                                    removal_policy=cdk.RemovalPolicy.DESTROY)
        

        myVpc.add_flow_log('CDK-3TA-FLOWLOG', destination = ec2.FlowLogDestination.to_cloud_watch_logs(logGroupFlow))

         
        logEC2Group =  log.LogGroup(self,'CDK-3TA-EC2-LOG-GROUP',
                                    log_group_name='CDK-3TA-EC2-LOG-GROUP',
                                    retention=log.RetentionDays.ONE_DAY,
                                    removal_policy=cdk.RemovalPolicy.DESTROY)
        log.MetricFilter(self, "CDK-3TA-EC2-LOG-GROUP-METRIC-FILTER",
                        log_group=logEC2Group,
                        metric_namespace="general/lines",
                        metric_name="web1",
                        filter_pattern=log.FilterPattern.all_events(),
                        metric_value="1")


        webALBSecurityGroup = ec2.SecurityGroup(self,"WEB-ALB-SG",vpc=myVpc,allow_all_outbound=True)
        webALBSecurityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), connection=ec2.Port.tcp(80))      

        webSecurityGroup = ec2.SecurityGroup(self,"WEB-SG",vpc=myVpc,allow_all_outbound=True)
        webSecurityGroup.add_ingress_rule(webALBSecurityGroup,connection=ec2.Port.tcp(80))

        appALBSecurityGroup = ec2.SecurityGroup(self,"APP-ALB-SG",vpc=myVpc,allow_all_outbound=True)
        appALBSecurityGroup.add_ingress_rule(webSecurityGroup,connection=ec2.Port.tcp(80))      

        appSecurityGroup = ec2.SecurityGroup(self,"APP-SG",vpc=myVpc,allow_all_outbound=True)
        appSecurityGroup.add_ingress_rule(appALBSecurityGroup,connection=ec2.Port.tcp(80)) 

        rdsSecurityGroup = ec2.SecurityGroup(self,"RDS-SG",vpc=myVpc,allow_all_outbound=True)
        rdsSecurityGroup.add_ingress_rule(appSecurityGroup,connection=ec2.Port.tcp(3306)) 

        

        dbTierRDS = MySQLRDS(   stack=self,vpc=myVpc,
                                hostType="t2.micro",
                                dbName="db3ta",
                                dbGbSize=5,
                                securityGroup=rdsSecurityGroup)

        dbAccessSecretName = dbTierRDS.getSecretName()

        appTierEC2 = AppTierEC2(stack=self,vpc=myVpc,hostType="t2.micro",
                                dbAccessSecretName=dbAccessSecretName,
                                appSecurityGroup=appSecurityGroup,
                                albSecurityGroup=appALBSecurityGroup)

        appELBDNS = appTierEC2.getLoadBalancerDNS()
        WebTierEC2( stack=self,vpc=myVpc,hostType="t2.micro",
                    appDNS=appELBDNS,
                    webSecurityGroup=webSecurityGroup,
                    albSecurityGroup=webALBSecurityGroup)




        
        

       





