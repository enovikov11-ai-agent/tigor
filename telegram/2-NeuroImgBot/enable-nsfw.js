const { readFileSync, writeFileSync } = require('fs'),
    path = `../anaconda3/envs/neuroimgbot/lib/python3.8/site-packages/diffusers/pipelines/stable_diffusion/safety_checker.py`;

writeFileSync(path, readFileSync(path, 'utf-8')
    .replace('images[has_nsfw_concepts] = 0.0  # black image', 'liberty = True')
    .replace('if has_nsfw_concept:', 'if False:')
    .replace('if any(has_nsfw_concepts):', 'if False:')
);