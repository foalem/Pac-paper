import * as aws from "@pulumi/aws";
import type { PulumiApp, PulumiAppModule } from "@webiny/pulumi";
import { createAppModule } from "@webiny/pulumi";

export type BlueGreenRouterApiGateway = PulumiAppModule<typeof BlueGreenRouterApiGateway>;

export interface IBlueGreenRouterApiGatewayParams {
    region: aws.Provider;
    protect: boolean;
}

export const BlueGreenRouterApiGateway = createAppModule({
    name: "BlueGreenRouterApiGateway",
    config(app: PulumiApp, params: IBlueGreenRouterApiGatewayParams) {
        const apiGateway = app.addResource(aws.apigatewayv2.Api, {
            name: "blueGreenRouterApi",
            opts: {
                protect: params.protect,
                provider: params.region
            },
            config: {
                protocolType: "HTTP",
                description: "Blue / Green Router API"
            }
        });

        const apiStage = app.addResource(aws.apigatewayv2.Stage, {
            name: "blue-green-stage",
            opts: {
                protect: params.protect,
                provider: params.region
            },
            config: {
                apiId: apiGateway.output.id,
                autoDeploy: true,
                name: app.params.run.env,
                defaultRouteSettings: {
                    // Only enable when debugging. Note that by default, API Gateway does not
                    // have the required permissions to write logs to CloudWatch logs. More:
                    // https://coady.tech/aws-cloudwatch-logs-arn/
                    // loggingLevel: "INFO",
                    throttlingBurstLimit: 5000,
                    throttlingRateLimit: 10000
                }
            }
        });

        return {
            apiStage,
            apiGateway
        };
    }
});
