#!/usr/bin/env python3



from aws_cdk import core

from cdk_3_ta.cdk_3_ta_stack import Cdk3TaStack


app = core.App()

#getting account id and region id from AWS CLI configuration
accountID = core.Aws.ACCOUNT_ID
regionID = core.Aws.REGION

Cdk3TaStack(app, "CDK-3TA-Stack",
            env=core.Environment(account=accountID, region=regionID))

app.synth()
