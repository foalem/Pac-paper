import * as aws from "@pulumi/aws";
import { isResourceOfType, PulumiAppParam } from "@webiny/pulumi";
import { License } from "@webiny/wcp";
import {
    createApiPulumiApp as baseCreateApiPulumiApp,
    CreateApiPulumiAppParams as BaseCreateApiPulumiAppParams
} from "~/apps/api/createApiPulumiApp";
import { handleGuardDutyEvents } from "~/enterprise/api/handleGuardDutyEvents";

export type ApiPulumiApp = ReturnType<typeof createApiPulumiApp>;

export type ApiPulumiAppAdvancedVpcParams = Partial<{
    useExistingVpc: {
        lambdaFunctionsVpcConfig: aws.types.input.lambda.FunctionVpcConfig;
    };
}>;

export interface CreateApiPulumiAppParams extends Omit<BaseCreateApiPulumiAppParams, "vpc"> {
    vpc?: PulumiAppParam<boolean | ApiPulumiAppAdvancedVpcParams>;
}

export function createApiPulumiApp(projectAppParams: CreateApiPulumiAppParams = {}) {
    return baseCreateApiPulumiApp({
        ...projectAppParams,
        // If using existing VPC, we ensure `vpc` param is set to `false`.
        vpc: ({ getParam }) => {
            const vpc = getParam(projectAppParams.vpc);
            if (!vpc) {
                // This could be `false` or `undefined`. If `undefined`, down the line,
                // this means "deploy into VPC if dealing with a production environment".
                return vpc;
            }

            // If using an existing VPC, we ensure Webiny does not deploy its own VPC.
            const usingAdvancedVpcParams = typeof vpc !== "boolean";
            if (usingAdvancedVpcParams && vpc.useExistingVpc) {
                return false;
            }

            return true;
        },
        async pulumi(app) {
            const license = await License.fromEnvironment();

            const { getParam } = app;
            const vpc = getParam(projectAppParams.vpc);
            const usingAdvancedVpcParams = vpc && typeof vpc !== "boolean";

            if (license.canUseFileManagerThreatDetection()) {
                handleGuardDutyEvents(app);
            }

            // Not using advanced VPC params? Then immediately exit.
            if (!usingAdvancedVpcParams) {
                return projectAppParams.pulumi?.(app);
            }

            const { onResource, addResource } = app;
            const { useExistingVpc } = vpc;

            // 1. We first deal with "existing VPC" setup.
            if (useExistingVpc) {
                if (!useExistingVpc.lambdaFunctionsVpcConfig) {
                    throw new Error(
                        "Cannot specify `useExistingVpc` parameter because the `lambdaFunctionsVpcConfig` parameter wasn't provided."
                    );
                }

                onResource(resource => {
                    if (isResourceOfType(resource, aws.lambda.Function)) {
                        const canUseVpc = resource.meta.canUseVpc !== false;
                        if (canUseVpc) {
                            resource.config.vpcConfig(useExistingVpc!.lambdaFunctionsVpcConfig);
                        }
                    }

                    if (isResourceOfType(resource, aws.iam.Role)) {
                        if (resource.meta.isLambdaFunctionRole) {
                            addResource(aws.iam.RolePolicyAttachment, {
                                name: `${resource.name}-vpc-access-execution-role`,
                                config: {
                                    role: resource.output.name,
                                    policyArn: aws.iam.ManagedPolicy.AWSLambdaVPCAccessExecutionRole
                                }
                            });
                        }
                    }
                });
            }

            return projectAppParams.pulumi?.(app);
        }
    });
}
