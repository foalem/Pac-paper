import * as aws from "@pulumi/aws";
import { type PulumiApp, type PulumiAppResource } from "@webiny/pulumi";
import type { IResolvedDomains } from "~/apps/blueGreen/types.js";

export interface IAttachDomainsToOutputParams {
    app: PulumiApp;
    domains: IResolvedDomains;
    cloudFront: PulumiAppResource<typeof aws.cloudfront.Distribution>;
}

export const attachDomainsToOutput = (params: IAttachDomainsToOutputParams) => {
    const { app, cloudFront } = params;

    app.addHandler(() => {
        const distributionDomain = cloudFront.output.domainName;
        const distributionUrl = distributionDomain.apply(value => `https://${value}`);

        app.addOutputs({
            ["distributionDomain"]: distributionDomain,
            ["distributionUrl"]: distributionUrl,
            ["environments"]: params.domains,
            ["domains"]: []
        });
        // We're adjusting the outputs via the `config.aliases` setter.
        // At the time of implementing this, could not find a better solution.
        cloudFront.config.aliases(aliases => {
            const domains: string[] = [];

            for (const alias of aliases || []) {
                domains.push(alias);
            }

            app.addOutputs({
                ["domains"]: domains
            });

            return aliases;
        });
    });
};
