import * as aws from "@pulumi/aws";
import type { PulumiApp, PulumiAppModule } from "@webiny/pulumi";
import { createAppModule } from "@webiny/pulumi";

export type BlueGreenRouterCloudFrontStore = PulumiAppModule<typeof BlueGreenRouterCloudFrontStore>;

export interface IBlueGreenRouterCloudFrontStoreParams {
    region: aws.Provider;
    protect: boolean;
}

export const BlueGreenRouterCloudFrontStore = createAppModule({
    name: "BlueGreenRouterCloudFrontStore",
    config(app: PulumiApp, params: IBlueGreenRouterCloudFrontStoreParams) {
        const cloudFrontStore = app.addResource(aws.cloudfront.KeyValueStore, {
            name: "blueGreenRouterCloudFrontStore",
            opts: {
                provider: params.region,
                protect: params.protect
            },
            config: {}
        });

        return {
            cloudFrontStore
        };
    }
});
