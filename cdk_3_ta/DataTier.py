

import aws_cdk.core as cdk
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_rds as rds


#this class encapsulates the CDK logic to build a DB Tier
class MySQLRDS:



    def __init__(self,stack: cdk.Stack,vpc: ec2.Vpc, hostType: str,dbName: str,
                dbGbSize: int,securityGroup: ec2.SecurityGroup) -> None:
  
        #define which MySQL engine we use
        instanceEngine = rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_23)
        #define compute class type
        instanceType = ec2.InstanceType(instance_type_identifier=hostType)

       
           
        #Create RDS database instance
        myDB=rds.DatabaseInstance(stack,"RDS-DB",
                                engine=instanceEngine,
                                vpc=vpc,
                                allow_major_version_upgrade=False,#no major versions automatic upgrades
                                auto_minor_version_upgrade=True,#yes minor versions automatic upgrades
                                multi_az=True,# high availability...please
                                instance_type=instanceType,
                                database_name=dbName,
                                allocated_storage=dbGbSize,
                                removal_policy=cdk.RemovalPolicy.DESTROY,
                                deletion_protection=False,
                                backup_retention=cdk.Duration.days(0),#no backups..it's only a test
                                security_groups=[securityGroup])

       
       
        #retrieve created secret name to be shared with App tier resources
        self.__databaseSecretName = myDB.node.find_child("Secret").secret_name
    
    #public method to return database secret name
    def getSecretName(self):
        return self.__databaseSecretName

        
