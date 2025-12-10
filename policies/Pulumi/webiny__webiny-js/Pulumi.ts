import { createPreset } from "../createPreset";

export const pulumi = createPreset(() => {
    return {
        name: "pulumi",
        matching: /^@pulumi\//,
        skipResolutions: true
    };
});
