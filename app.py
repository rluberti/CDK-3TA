#!/usr/bin/env python3



from aws_cdk import core

from cdk_3_ta.cdk_3_ta_stack import Cdk3TaStack


app = core.App()
Cdk3TaStack(app, "CDK-3TA-Stack",

#enter your account id here
env=core.Environment(account='enter your AWS Account ID', region='us-east-1'))



app.synth()
