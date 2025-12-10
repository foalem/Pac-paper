import * as aws from "@pulumi/aws";
import type { QueueArgs } from "@pulumi/aws/sqs";
import type { PulumiApp } from "@webiny/pulumi";
import { createAppModule } from "@webiny/pulumi";

export interface ISyncSystemSQSParams {
    protect: boolean;
}

export const SyncSystemSQS = createAppModule({
    name: "SyncSystemSQS",
    config: (app: PulumiApp, params: ISyncSystemSQSParams) => {
        const config: QueueArgs = {
            delaySeconds: 0,
            visibilityTimeoutSeconds: 900,
            fifoQueue: true,
            receiveWaitTimeSeconds: 0,
            /**
             * The maximum message size is 256 KB.
             * Is it enough? If not, we can use S3 to store the message and only store the reference in the queue.
             */
            maxMessageSize: 262144, // max
            /**
             * How log do we keep the message in the queue?
             * Something is very wrong if the message is not processed within 4 days... :/
             */
            messageRetentionSeconds: 345600 // default - 4 days
        };
        return app.addResource(aws.sqs.Queue, {
            name: "sync-sqs",
            config,
            opts: {
                protect: params.protect
            }
        });
    }
});
