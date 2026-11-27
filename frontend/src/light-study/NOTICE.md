# Animated light study

Adapted from **Volumetric Light and Bones animation by Cullen Webber**:

- https://github.com/cullenwebber/three-volumetric-light
- https://cullenwebber.github.io/three-volumetric-light/
- Pinned commit: `28b2103f1ce0403eacbe53c4ea53790b8905705a`

The hand model, finger/wrist animation, volumetric beam, particles, ASCII material and postprocessing originate in that reference. Their authorship is not claimed by this project. `UPSTREAM.json` records the original source hashes and hand-model hash.

ChequeVerify replaces the floating kanji geometry with its C/check outline. Adaptations also cover local model/Draco paths, Vite raw-shader imports, removal of unused experimental shading, reduced-motion handling and a 30fps/hidden-page render limit. The scene runs in a local child document so Enter removes the renderer, animation loop and listeners together. Three.js 0.182.0 matches the reference's shadow-depth texture implementation.

This is decorative opening artwork, independent of recognition outputs. The generated still-hand replacement is removed. Parent-page captions stay removed; the Enter arrow remains keyboard accessible.
