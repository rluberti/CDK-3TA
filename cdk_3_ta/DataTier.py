from aws_cdk.aws_iam import IGrantable, ManagedPolicy
import  aws_cdk.aws_secretsmanager as sm
import aws_cdk.core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_autoscaling as autos

import aws_cdk.aws_rds as rds
from jsii import Number








class MySQLRDS:



    def __init__(self,stack: cdk.Stack,vpc: ec2.Vpc, hostType: str,dbName: str,
                dbGbSize: int,securityGroup: ec2.SecurityGroup) -> None:
  
#   Credentials = Credentials.FromPassword(
#                     username: "adminuser", 
#                     password: new SecretValue("Admin12345?")),

        instanceEngine = rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_23)
        instanceType = ec2.InstanceType(instance_type_identifier=hostType)

       
           

        myDB=rds.DatabaseInstance(stack,"RDS-DB",
                                engine=instanceEngine,
                                vpc=vpc,
                                allow_major_version_upgrade=False,
                                auto_minor_version_upgrade=True,
                                multi_az=True,
                                instance_type=instanceType,
                                database_name=dbName,
                                allocated_storage=dbGbSize,
                                removal_policy=cdk.RemovalPolicy.DESTROY,
                                deletion_protection=False,
                                backup_retention=cdk.Duration.days(0),
                                security_groups=[securityGroup])

       
       
        
        self.__databaseSecretName = myDB.node.find_child("Secret").secret_name


        cdk.CfnOutput(stack, "myDB.secret_arn",description="Secret ARN", value=myDB.secret.secret_arn)
        cdk.CfnOutput(stack, "myDB.instance_arn",description="Instance ARN", value=myDB.instance_arn)
        

        cdk.CfnOutput(stack, "myDB.secret_name",description="secret key to share", value=self.__databaseSecretName)

       
        
    def getSecretName(self):
        return self.__databaseSecretName

        
